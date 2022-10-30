
from collections import deque
from math import floor

import numpy as np

from datatrader.price_parser import PriceParser
from datatrader.event import (SignalEvent, EventType)
from datatrader.strategy.base import AbstractStrategy


class CointegrationBollingerBandsStrategy(AbstractStrategy):
    """
    Requisiti:
    tickers - La lista dei simboli dei ticker
    events_queue - Manager del sistema della coda degli eventi
    lookback - Periodo di lookback per la media mobile e deviazione standard
    weights - Il vettore dei pesi che descrive le "unità" del portafoglio
    entry_z - La soglia z-score per entrare nel trade
    exit_z - La soglia z-score per uscire dal trade
    base_quantity - Numero di "unità" di un portafoglio che sono negoziate
    """
    def __init__(
        self, tickers, events_queue,
        lookback, weights, entry_z, exit_z,
        base_quantity
    ):
        self.tickers = tickers
        self.events_queue = events_queue
        self.lookback = lookback
        self.weights = weights
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.qty = base_quantity
        self.time = None
        self.latest_prices = np.full(len(self.tickers), -1.0)
        self.port_mkt_val = deque(maxlen=self.lookback)
        self.invested = None
        self.bars_elapsed = 0

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
            for i in range(0, len(self.tickers)):
                if event.ticker == self.tickers[i]:
                    self.latest_prices[i] = price
        else:
            self.time = event.time
            self.bars_elapsed += 1
            self.latest_prices = np.full(len(self.tickers), -1.0)
            for i in range(0, len(self.tickers)):
                if event.ticker == self.tickers[i]:
                    self.latest_prices[i] = price

    def go_long_units(self):
        """
        Andiamo long con il numero appropriato di "unità" del portafoglio
        per aprire una nuova posizione o chiudere una posizione short.
        """
        for i, ticker in enumerate(self.tickers):
            if self.weights[i] < 0.0:
                self.events_queue.put(SignalEvent(
                    ticker, "SLD",
                    int(floor(-1.0 * self.qty * self.weights[i])))
                )
            else:
                self.events_queue.put(SignalEvent(
                    ticker, "BOT",
                    int(floor(self.qty * self.weights[i])))
                )

    def go_short_units(self):
        """
        Andare short del numero appropriato di "unità" del portafoglio
        per aprire una nuova posizione o chiudere una posizione long.
        """
        for i, ticker in enumerate(self.tickers):
            if self.weights[i] < 0.0:
                self.events_queue.put(SignalEvent(
                    ticker, "BOT",
                    int(floor(-1.0 * self.qty * self.weights[i])))
                )
            else:
                self.events_queue.put(SignalEvent(
                    ticker, "SLD",
                    int(floor(self.qty * self.weights[i])))
                )

    def zscore_trade(self, zscore, event):
        """
        Determina il trade se la soglia dello zscore di
        entrata o di uscita è stata superata.
        """
        # Se non siamo a mercato
        if self.invested is None:
            if zscore < -self.entry_z:
                # Entrata Long
                print("LONG: %s" % event.time)
                self.go_long_units()
                self.invested = "long"
            elif zscore > self.entry_z:
                # Entrata Short
                print("SHORT: %s" % event.time)
                self.go_short_units()
                self.invested = "short"
        # Se siamo a mercato
        if self.invested is not None:
            if self.invested == "long" and zscore >= -self.exit_z:
                print("CLOSING LONG: %s" % event.time)
                self.go_short_units()
                self.invested = None
            elif self.invested == "short" and zscore <= self.exit_z:
                print("CLOSING SHORT: %s" % event.time)
                self.go_long_units()
                self.invested = None

    def calculate_signals(self, event):
        """
        Calcula i segnali della strategia.
        """
        if event.type == EventType.BAR:
            self._set_correct_time_and_price(event)

            # Operiamo sono se abbiamo tutti i prezzi
            if all(self.latest_prices > -1.0):
                # Calcoliamo il valore di mercato del portfolio tramite il prodotto
                # cartesiamo dei prezzi degli ETF e dei relativi pesi nel portafoglio
                self.port_mkt_val.append(
                    np.dot(self.latest_prices, self.weights)
                )
                # Se ci sono sufficienti dati per formare una completa finestra di ricerca,
                # calcola lo zscore ed esegue le rispettive operazioni se le soglie vengono superate
                if self.bars_elapsed > self.lookback:
                    zscore = (self.port_mkt_val[-1] - np.mean(self.port_mkt_val)
                             ) / np.std(self.port_mkt_val)
                    self.zscore_trade(zscore, event)