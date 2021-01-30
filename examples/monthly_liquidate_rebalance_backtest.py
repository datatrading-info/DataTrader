import datetime

from datatrader import settings
from datatrader.position_sizer.rebalance import LiquidateRebalancePositionSizer
from datatrader.compat import queue
from datatrader.trading_session import TradingSession

from .strategies.monthly_liquidate_rebalance_strategy import MonthlyLiquidateRebalanceStrategy


def run(config, testing, tickers, filename):
    # Backtest information
    title = [
        'Portafoglio di 60%/40% SPY/AGG con Ribilanciamento Mensile'
    ]
    initial_equity = 500000.0
    start_date = datetime.datetime(2006, 11, 1)
    end_date = datetime.datetime(2016, 10, 12)

    # Usa la strategia Monthly Liquidate And Rebalance
    events_queue = queue.Queue()
    strategy = MonthlyLiquidateRebalanceStrategy(
        tickers, events_queue
    )

    # Usa il sizer delle posizione di liquidazioni e ribilanciamento
    # con pesi dei ticker predefiniti
    ticker_weights = {
        "SPY": 0.6,
        "AGG": 0.4,
    }
    position_sizer = LiquidateRebalancePositionSizer(
        ticker_weights
    )

    # Setup del backtest
    backtest = TradingSession(
        config, strategy, tickers,
        initial_equity, start_date, end_date,
        events_queue, position_sizer=position_sizer,
        title=title, benchmark=tickers[0],
    )
    results = backtest.start_trading(testing=testing)
    return results


if __name__ == "__main__":
    # Dati di configurazione
    testing = False
    config = settings.from_file(
        settings.DEFAULT_CONFIG_FILENAME, testing
    )
    tickers = ["SPY", "AGG"]
    filename = None
    run(config, testing, tickers, filename)
