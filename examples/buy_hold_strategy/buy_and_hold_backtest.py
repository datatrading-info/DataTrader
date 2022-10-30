import datetime

from datatrader import settings
from datatrader.strategy.base import AbstractStrategy
from datatrader.event import SignalEvent, EventType
from datatrader.compat import queue
from datatrader.trading_session import TradingSession


class BuyAndHoldStrategy(AbstractStrategy):
    """
    Una strategia di test che si limita ad acquistare (long) un
    asset alla prima ricezione dell'evento bar in questione e
    quindi mantiene la posizione fino al completamento del backtest.
    """
    def __init__(
        self, ticker, events_queue,
        base_quantity=100
    ):
        self.ticker = ticker
        self.events_queue = events_queue
        self.base_quantity = base_quantity
        self.bars = 0
        self.invested = False

    def calculate_signals(self, event):
        if (
            event.type in [EventType.BAR, EventType.TICK] and
            event.ticker == self.ticker
        ):
            if not self.invested and self.bars == 0:
                signal = SignalEvent(
                    self.ticker, "BOT",
                    suggested_quantity=self.base_quantity
                )
                self.events_queue.put(signal)
                self.invested = True
            self.bars += 1


def run(config, testing, tickers, filename):
    # informazioni del Backtest
    title = ['Buy and Hold Example on %s' % tickers[0]]
    initial_equity = 10000.0
    start_date = datetime.datetime(2000, 1, 1)
    end_date = datetime.datetime(2014, 1, 1)

    # Uso della strategia Buy and Hold
    events_queue = queue.Queue()
    strategy = BuyAndHoldStrategy(tickers[0], events_queue)

    # Setup del backtest
    backtest = TradingSession(
        config, strategy, tickers,
        initial_equity, start_date, end_date,
        events_queue, title=title
    )
    results = backtest.start_trading(testing=testing)
    return results


if __name__ == "__main__":
    # Dati di configurazione
    testing = False
    config = settings.from_file(
        settings.DEFAULT_CONFIG_FILENAME, testing
    )
    tickers = ["SPY"]
    filename = None
    run(config, testing, tickers, filename)

