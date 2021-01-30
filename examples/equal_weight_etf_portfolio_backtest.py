
import datetime

from datatrader import settings
from monthly_rebalance_run import run_monthly_rebalance


if __name__ == "__main__":
    ticker_weights = {
        "SPY": 0.125,
        "IJS": 0.125,
        "EFA": 0.125,
        "EEM": 0.125,
        "AGG": 0.125,
        "JNK": 0.125,
        "DJP": 0.125,
        "RWR": 0.125
    }
    run_monthly_rebalance(
        settings.DEFAULT_CONFIG_FILENAME, False, "",
        "SPY", ticker_weights, "Strategia con uguale percentuale di ETF",
        datetime.datetime(2007, 12, 4), datetime.datetime(2016, 10, 12),
        500000.00
    )