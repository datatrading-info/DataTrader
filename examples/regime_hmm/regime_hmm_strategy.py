# regime_hmm_strategy.py

from collections import deque

import numpy as np

from datatrader.price_parser import PriceParser
from datatrader.event import SignalEvent, EventType
from datatrader.strategy.base import AbstractStrategy

class MovingAverageCrossStrategy(AbstractStrategy):
    """
    Requisiti:
    tickers - La lista dei simboli dei ticker
    events_queue - Il manager della coda degli eventi
    short_window - Periodo di lookback per la media mobile breve
    long_window - Periodo di lookback per la media mobile lunga
    """
    def __init__(
        self, tickers,
        events_queue, base_quantity,
        short_window=10, long_window=30
    ):
        self.tickers = tickers
        self.events_queue = events_queue
        self.base_quantity = base_quantity
        self.short_window = short_window
        self.long_window = long_window
        self.bars = 0
        self.invested = False
        self.sw_bars = deque(maxlen=self.short_window)
        self.lw_bars = deque(maxlen=self.long_window)

    def calculate_signals(self, event):
        # Applica SMA al primo ticker
        ticker = self.tickers[0]
        if event.type == EventType.BAR and event.ticker == ticker:
            # Aggiunge l'ultimo prezzo di chiusura ai dati
            # delle finestre corta e lunga
            price = event.adj_close_price / PriceParser.PRICE_MULTIPLIER
            self.lw_bars.append(price)
            if self.bars > self.long_window - self.short_window:
                self.sw_bars.append(price)

            # Sono presenti abbastanza barre per il trading
            if self.bars > self.long_window:
                # Calcola le medie mobili semplici
                short_sma = np.mean(self.sw_bars)
                long_sma = np.mean(self.lw_bars)
                # Segnali di trading basati sulla media mobile incrociata
                if short_sma > long_sma and not self.invested:
                    print("LONG: %s" % event.time)
                    signal = SignalEvent(ticker, "BOT", self.base_quantity)
                    self.events_queue.put(signal)
                    self.invested = True
                elif short_sma < long_sma and self.invested:
                    print("SHORT: %s" % event.time)
                    signal = SignalEvent(ticker, "SLD", self.base_quantity)
                    self.events_queue.put(signal)
                    self.invested = False
            self.bars += 1