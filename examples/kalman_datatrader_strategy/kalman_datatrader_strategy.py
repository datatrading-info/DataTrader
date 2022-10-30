
from math import floor
import numpy as np

from datatrader.price_parser import PriceParser
from datatrader.event import (SignalEvent, EventType)
from datatrader.strategy.base import AbstractStrategy


class KalmanPairsTradingStrategy(AbstractStrategy):
    """
    Requisiti:
    tickers - Lista dei simboli dei ticker
    events_queue - Manager del sistema della coda degli eventi
    short_window - numero di barre per la moving average di breve periodo
    long_window - numero di barre per la moving average di lungo periodo
    """
    def __init__(
        self, tickers, events_queue
    ):
        self.tickers = tickers
        self.events_queue = events_queue
        self.time = None
        self.latest_prices = np.array([-1.0, -1.0])
        self.invested = None

        self.delta = 1e-4
        self.wt = self.delta / (1 - self.delta) * np.eye(2)
        self.vt = 1e-3
        self.theta = np.zeros(2)
        self.P = np.zeros((2, 2))
        self.R = None
        self.C = None

        self.days = 0
        self.qty = 2000
        self.cur_hedge_qty = self.qty

    def _set_correct_time_and_price(self, event):
        """
        Impostazione del corretto prezzo e timestamp dell'evento
        estratto in ordine dalla coda degli eventi.
        """
        # Impostazione della prima istanza di time
        if self.time is None:
            self.time = event.time

        # Correzione degli ultimi prezzi, che dipendono dall'ordine in cui
        # arrivano gli eventi delle barre di mercato
        price = event.adj_close_price / PriceParser.PRICE_MULTIPLIER
        if event.time == self.time:
            if event.ticker == self.tickers[0]:
                self.latest_prices[0] = price
            else:
                self.latest_prices[1] = price
        else:
            self.time = event.time
            self.days += 1
            self.latest_prices = np.array([-1.0, -1.0])
            if event.ticker == self.tickers[0]:
                self.latest_prices[0] = price
            else:
                self.latest_prices[1] = price

    def calculate_signals(self, event):
        """
        Calculo dei segnali della stategia con il filtro di Kalman.
        """
        if event.type == EventType.BAR:
            self._set_correct_time_and_price(event)

            # Opera solo se abbiamo entrambe le osservazioni
            if all(self.latest_prices > -1.0):
                # Creare la matrice di osservazione degli ultimi prezzi di
                # TLT e il valore dell'intercetta nonché il
                # valore scalare dell'ultimo prezzo di IEI
                F = np.asarray([self.latest_prices[0], 1.0]).reshape((1, 2))
                y = self.latest_prices[1]

                # Il valore a priori degli stati \theta_t è una distribuzione
                # gaussiana multivariata con media a_t e varianza-covarianza R_t
                if self.R is not None:
                    self.R = self.C + self.wt
                else:
                    self.R = np.zeros((2, 2))

                # Calcola l'aggiornamento del filtro di Kalman
                # ----------------------------------
                # Calcola la previsione di una nuova osservazione
                # e il relativo errore di previsione
                yhat = F.dot(self.theta)
                et = y - yhat

                # Q_t è la varianza della previsione delle osservazioni
                # e sqrt{Q_t} è la deviazione standard delle previsioni
                Qt = F.dot(self.R).dot(F.T) + self.vt
                sqrt_Qt = np.sqrt(Qt)

                # Il valore a posteriori degli stati \theta_t ha una
                # distribuzione gaussiana multivariata con
                # media m_t e varianza-covarianza C_t
                At = self.R.dot(F.T) / Qt
                self.theta = self.theta + At.flatten() * et
                self.C = self.R - At * F.dot(self.R)

                # Opera solo se i giorni sono maggiori del
                # periodo di "riscaldamento"
                if self.days > 1:
                    # Se non siamo a mercato...
                    if self.invested is None:
                        if et < -sqrt_Qt:
                            # Entrata Long
                            print("LONG: %s" % event.time)
                            self.cur_hedge_qty = int(floor(self.qty*self.theta[0]))
                            self.events_queue.put(SignalEvent(self.tickers[1], "BOT", self.qty))
                            self.events_queue.put(SignalEvent(self.tickers[0], "SLD", self.cur_hedge_qty))
                            self.invested = "long"
                        elif et > sqrt_Qt:
                            # Entrata Short
                            print("SHORT: %s" % event.time)
                            self.cur_hedge_qty = int(floor(self.qty*self.theta[0]))
                            self.events_queue.put(SignalEvent(self.tickers[1], "SLD", self.qty))
                            self.events_queue.put(SignalEvent(self.tickers[0], "BOT", self.cur_hedge_qty))
                            self.invested = "short"
                    # Se siamo a mercato...
                    if self.invested is not None:
                        if self.invested == "long" and et > -sqrt_Qt:
                            print("CLOSING LONG: %s" % event.time)
                            self.events_queue.put(SignalEvent(self.tickers[1], "SLD", self.qty))
                            self.events_queue.put(SignalEvent(self.tickers[0], "BOT", self.cur_hedge_qty))
                            self.invested = None
                        elif self.invested == "short" and et < sqrt_Qt:
                            print("CLOSING SHORT: %s" % event.time)
                            self.events_queue.put(SignalEvent(self.tickers[1], "BOT", self.qty))
                            self.events_queue.put(SignalEvent(self.tickers[0], "SLD", self.cur_hedge_qty))
                            self.invested = None
