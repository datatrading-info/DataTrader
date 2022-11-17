# regime_hmm_backtest.py

import click
import datetime
import pickle

from datatrader import settings
from datatrader.compat import queue
from datatrader.price_parser import PriceParser
from datatrader.price_handler.yahoo_daily_csv_bar import YahooDailyCsvBarPriceHandler
from datatrader.strategy.base import Strategies
from datatrader.position_sizer.naive import NaivePositionSizer
from datatrader.risk_manager.example import ExampleRiskManager
from datatrader.portfolio_handler import PortfolioHandler
from datatrader.compliance.example import ExampleCompliance
from datatrader.execution_handler.ib_simulated import IBSimulatedExecutionHandler
from datatrader.statistics.tearsheet import TearsheetStatistics
from datatrader.trading_session import TradingSession

from regime_hmm_strategy import MovingAverageCrossStrategy
from regime_hmm_risk_manager import RegimeHMMRiskManager


def run(config, testing, tickers, filename):
    # Impostazione delle variabili necessarie al backtest
    pickle_path = "/path/to/your/model/hmm_model_spy.pkl"
    events_queue = queue.Queue()
    csv_dir = config.CSV_DATA_DIR
    initial_equity = PriceParser.parse(500000.00)

    # uso del Use Yahoo Daily Price Handler
    start_date = datetime.datetime(2005, 1, 1)
    end_date = datetime.datetime(2014, 12, 31)
    price_handler = YahooDailyCsvBarPriceHandler(
        csv_dir, events_queue, tickers,
        start_date=start_date, end_date=end_date,
        calc_adj_returns=True
    )

    # Uso della strategia Moving Average Crossover
    base_quantity = 10000
    strategy = MovingAverageCrossStrategy(
        tickers, events_queue, base_quantity,
        short_window=10, long_window=30
    )
    strategy = Strategies(strategy)

    # Uso di un Position Sizer standard
    position_sizer = NaivePositionSizer()

    # Uso del Risk Manager di determinazione del regime HMM
    hmm_model = pickle.load(open(pickle_path, "rb"))
    risk_manager = RegimeHMMRiskManager(hmm_model)
    # Uso di un Risk Manager di esempio
    #risk_manager = ExampleRiskManager()

    # Use del Manager di Portfolio di default
    portfolio_handler = PortfolioHandler(
        PriceParser.parse(initial_equity), events_queue, price_handler,
        position_sizer, risk_manager
    )

    # Uso del componente ExampleCompliance
    compliance = ExampleCompliance(config)

    # Uso un Manager di Esecuzione che simula IB
    execution_handler = IBSimulatedExecutionHandler(
        events_queue, price_handler, compliance
    )

    # Uso delle statistiche di default
    title = ["Trend Following Regime Detection with HMM"]
    statistics = TearsheetStatistics(
        config, portfolio_handler, title,
        benchmark="SPY"
    )

    # Settaggio del backtest
    backtest = TradingSession(
        config, strategy, tickers,
        initial_equity, start_date, end_date, events_queue,
        price_handler=price_handler,
        portfolio_handler=portfolio_handler,
        compliance=compliance,
        position_sizer=position_sizer,
        execution_handler=execution_handler,
        risk_manager=risk_manager,
        statistics=statistics,
        sentiment_handler=None,
        title=title, benchmark='SPY'
    )
    results = backtest.start_trading(testing=testing)
    statistics.save(filename)
    return results


@click.command()
@click.option('--config', default=settings.DEFAULT_CONFIG_FILENAME, help='Config filename')
@click.option('--testing/--no-testing', default=False, help='Enable testing mode')
@click.option('--tickers', default='SPY', help='Tickers (use comma)')
@click.option('--filename', default='', help='Pickle (.pkl) statistics filename')
def main(config, testing, tickers, filename):
    tickers = tickers.split(",")
    config = settings.from_file(config, testing)
    run(config, testing, tickers, filename)


if __name__ == "__main__":
    main()