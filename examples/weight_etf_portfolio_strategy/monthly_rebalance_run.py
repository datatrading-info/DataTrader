
from datatrader import settings
from datatrader.compat import queue
from datatrader.price_parser import PriceParser
from datatrader.price_handler.yahoo_daily_csv_bar import YahooDailyCsvBarPriceHandler
from examples.strategies.monthly_liquidate_rebalance_strategy import MonthlyLiquidateRebalanceStrategy

from datatrader.position_sizer.rebalance import LiquidateRebalancePositionSizer
from datatrader.risk_manager.example import ExampleRiskManager
from datatrader.portfolio_handler import PortfolioHandler
from datatrader.compliance.example import ExampleCompliance
from datatrader.execution_handler.ib_simulated import IBSimulatedExecutionHandler
from datatrader.statistics.tearsheet import TearsheetStatistics
from datatrader.trading_session import TradingSession


def run_monthly_rebalance(
    config, testing, filename,
    benchmark, ticker_weights, title_str,
    start_date, end_date, equity
):
    config = settings.from_file(config, testing)
    tickers = [t for t in ticker_weights.keys()]

    # Imposta le variabili necessarie per il backtest
    events_queue = queue.Queue()
    csv_dir = config.CSV_DATA_DIR
    initial_equity = PriceParser.parse(equity)

    # Uso di Yahoo Daily Price Handler
    price_handler = YahooDailyCsvBarPriceHandler(
        csv_dir, events_queue, tickers,
        start_date=start_date, end_date=end_date
    )

    # Uso della strategia "monthly liquidate Rebalance"
    strategy = MonthlyLiquidateRebalanceStrategy(tickers, events_queue)
   # strategy = Strategies(strategy, DisplayStrategy())

    # Uso del sizer delle posizioni con specifici pesi dei ticker
    position_sizer = LiquidateRebalancePositionSizer(ticker_weights)

    # Uso di un Risk Manager di esempio
    risk_manager = ExampleRiskManager()

    # Uso del Portfolio Handler standard
    portfolio_handler = PortfolioHandler(
        initial_equity, events_queue, price_handler,
        position_sizer, risk_manager
    )

    # Uso del componente ExampleCompliance
    compliance = ExampleCompliance(config)

    # Uso di un IB Execution Handler simulato
    execution_handler = IBSimulatedExecutionHandler(
        events_queue, price_handler, compliance
    )

    # Uso delle statistiche standard
    title = [title_str]
    statistics = TearsheetStatistics(
        config, portfolio_handler, title, benchmark
    )

    # Setup del backtest
    backtest = TradingSession(
        config, strategy, tickers,
        initial_equity, start_date, end_date,
        events_queue, price_handler=price_handler,
        position_sizer=position_sizer,
        execution_handler=execution_handler,
        title=title, benchmark=tickers[0],
    )
    results = backtest.start_trading(testing=testing)
    statistics.save(filename)
    return results