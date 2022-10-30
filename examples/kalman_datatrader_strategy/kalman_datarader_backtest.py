# kalman_datatrader_backtest.py

import datetime

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

from kalman_datatrader_strategy import KalmanPairsTradingStrategy

def run(config, testing, tickers, filename):

    # Impostazione delle variabili necessarie per il backtest
    # Informazioni sul Backtest
    title = ['Kalman Filter Example on TLT and IEI: 100x300']
    initial_equity = 100000.00
    start_date = datetime.datetime(2009, 8, 1)
    end_date = datetime.datetime(2016, 8, 1)
    events_queue = queue.Queue()

    # Uso del Manager dei Prezzi di Yahoo Daily
    price_handler = YahooDailyCsvBarPriceHandler(config.CSV_DATA_DIR, events_queue,
                                 tickers, start_date=start_date, end_date=end_date)

    # Uso della strategia KalmanPairsTrading
    strategy = KalmanPairsTradingStrategy(tickers, events_queue)
    strategy = Strategies(strategy)

    # Uso di un Position Sizer standard
    position_sizer = NaivePositionSizer()

    # Uso di Manager di Risk di esempio
    risk_manager = ExampleRiskManager()

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
    statistics = TearsheetStatistics(
        config, portfolio_handler, title=""
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
        title=title, benchmark=None
    )
    results = backtest.start_trading(testing=testing)
    statistics.save(filename)
    return results


def main(config, testing, tickers, filename):
    tickers = tickers.split(",")
    config = settings.from_file(config, testing)
    run(config, testing, tickers, filename)


if __name__ == "__main__":
    config = './datatrader.yml'
    testing = False
    tickers = 'TLT,IEI'
    filename = None
    main(config, testing, tickers, filename)
