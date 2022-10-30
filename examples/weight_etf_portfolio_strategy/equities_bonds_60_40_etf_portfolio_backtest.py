import datetime

from datatrader import settings
from monthly_rebalance_run import run_monthly_rebalance


if __name__ == "__main__":
    ticker_weights = {
        "SPY": 0.6,
        "AGG": 0.4,
    }
    run_monthly_rebalance(
        settings.DEFAULT_CONFIG_FILENAME, False, "",
        "SPY", ticker_weights, "Strategia ETF mix 60/40 Azioni/Obbligazioni USA",
        datetime.datetime(2003, 9, 29), datetime.datetime(2016, 10, 12),
        500000.00
    )