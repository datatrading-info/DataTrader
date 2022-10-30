from collections import deque
import datetime

import numpy as np

from datatrader import settings
from datatrader.strategy.base import AbstractStrategy
from datatrader.event import SignalEvent, EventType
from datatrader.compat import queue
from datatrader.trading_session import TradingSession


class MovingAverageCrossStrategy(AbstractStrategy):
    """
    Richiede:
     ticker - Il simbolo ticker utilizzato per le medie mobili
     events_queue - Un gestore per la coda degli eventi di sistema
     short_window - Periodo per media mobile breve
     long_window - Periodo per media mobile lunga
    """
    def __init__(
        self, ticker,
        events_queue,
        short_window=100,
        long_window=300,
        base_quantity=100
    ):
        self.ticker = ticker
        self.events_queue = events_queue
        self.short_window = short_window
        self.long_window = long_window
        self.base_quantity = base_quantity
        self.bars = 0
        self.invested = False
        self.sw_bars = deque(maxlen=self.short_window)
        self.lw_bars = deque(maxlen=self.long_window)

    def calculate_signals(self, event):
        if (
            event.type == EventType.BAR and
            event.ticker == self.ticker
        ):
            # Aggiunge l'ultimo prezzo di chiusura aggiustato alle barre
            # delle finestre dei periodi brevi e lunghi
            self.lw_bars.append(event.adj_close_price)
            if self.bars > self.long_window - self.short_window:
                self.sw_bars.append(event.adj_close_price)

            # Sono presenti sufficienti barre per il trading
            if self.bars > self.long_window:
                # Calcola le medie mobili semplici
                short_sma = np.mean(self.sw_bars)
                long_sma = np.mean(self.lw_bars)
                # Segnali di trading baasati sull'incrocio delle medie mobili
                if short_sma > long_sma and not self.invested:
                    print("LONG %s: %s" % (self.ticker, event.time))
                    signal = SignalEvent(
                        self.ticker, "BOT",
                        suggested_quantity=self.base_quantity
                    )
                    self.events_queue.put(signal)
                    self.invested = True
                elif short_sma < long_sma and self.invested:
                    print("SHORT %s: %s" % (self.ticker, event.time))
                    signal = SignalEvent(
                        self.ticker, "SLD",
                        suggested_quantity=self.base_quantity
                    )
                    self.events_queue.put(signal)
                    self.invested = False
            self.bars += 1


def run(config, testing, tickers, filename):
    # Informazioni sul Backtest
    title = ['Moving Average Crossover Example on AAPL: 100x300']
    initial_equity = 10000.0
    start_date = datetime.datetime(2000, 1, 1)
    end_date = datetime.datetime(2014, 1, 1)

    # Uso della strategia MAC
    events_queue = queue.Queue()
    strategy = MovingAverageCrossStrategy(
        tickers[0], events_queue,
        short_window=100,
        long_window=300
    )

    # Setup del backtest
    backtest = TradingSession(
        config, strategy, tickers,
        initial_equity, start_date, end_date,
        events_queue, title=title,
        benchmark=tickers[1],
    )
    results = backtest.start_trading(testing=testing)
    return results


if __name__ == "__main__":
    # Dati di configurazione
    testing = False
    config = settings.from_file(
        settings.DEFAULT_CONFIG_FILENAME, testing
    )
    tickers = ["AAPL", "SPY"]
    filename = None
    run(config, testing, tickers, filename)
