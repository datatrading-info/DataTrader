from __future__ import print_function
from datetime import datetime
from .compat import queue
from .event import EventType
from .price_handler.yahoo_daily_csv_bar import YahooDailyCsvBarPriceHandler
from .price_parser import PriceParser
from .position_sizer.fixed import FixedPositionSizer
from .risk_manager.example import ExampleRiskManager
from .portfolio_handler import PortfolioHandler
from .compliance.example import ExampleCompliance
from .execution_handler.ib_simulated import IBSimulatedExecutionHandler
from .statistics.tearsheet import TearsheetStatistics


class TradingSession(object):
    """
    Racchiude le impostazioni e i componenti per
    eseguire un backtest o una sessione di trading dal vivo.
    """
    def __init__(
        self, config, strategy, tickers,
        equity, start_date, end_date, events_queue,
        session_type="backtest", end_session_time=None,
        price_handler=None, portfolio_handler=None,
        compliance=None, position_sizer=None,
        execution_handler=None, risk_manager=None,
        statistics=None, sentiment_handler=None,
        title=None, benchmark=None
    ):
        """
        Imposta le variabili di backtest in base agli argomenti di input.
        """
        self.config = config
        self.strategy = strategy
        self.tickers = tickers
        self.equity = PriceParser.parse(equity)
        self.start_date = start_date
        self.end_date = end_date
        self.events_queue = events_queue
        self.price_handler = price_handler
        self.portfolio_handler = portfolio_handler
        self.compliance = compliance
        self.execution_handler = execution_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.statistics = statistics
        self.sentiment_handler = sentiment_handler
        self.title = title
        self.benchmark = benchmark
        self.session_type = session_type
        self._config_session()
        self.cur_time = None

        if self.session_type == "live":
            if self.end_session_time is None:
                raise Exception("Must specify an end_session_time when live trading")

    def _config_session(self):
        """
        Inizializza le classi necessarie utilizzate all'interno della sessione.
        """
        if self.price_handler is None and self.session_type == "backtest":
            self.price_handler = YahooDailyCsvBarPriceHandler(
                self.config.CSV_DATA_DIR, self.events_queue,
                self.tickers, start_date=self.start_date,
                end_date=self.end_date
            )

        if self.position_sizer is None:
            self.position_sizer = FixedPositionSizer()

        if self.risk_manager is None:
            self.risk_manager = ExampleRiskManager()

        if self.portfolio_handler is None:
            self.portfolio_handler = PortfolioHandler(
                self.equity,
                self.events_queue,
                self.price_handler,
                self.position_sizer,
                self.risk_manager
            )

        if self.compliance is None:
            self.compliance = ExampleCompliance(self.config)

        if self.execution_handler is None:
            self.execution_handler = IBSimulatedExecutionHandler(
                self.events_queue,
                self.price_handler,
                self.compliance
            )

        if self.statistics is None:
            self.statistics = TearsheetStatistics(
                self.config, self.portfolio_handler,
                self.title, self.benchmark
            )

    def _continue_loop_condition(self):
        if self.session_type == "backtest":
            return self.price_handler.continue_backtest
        else:
            return datetime.now() < self.end_session_time

    def _run_session(self):
        """
        Esegue un ciclo while infinito che esegue il
        polling della coda degli eventi e indirizza ogni
        evento al componente della strategia del gestore
        di esecuzione.
        Il ciclo continua fino a quando la coda degli
        eventi non è stata svuotata.
        """
        if self.session_type == "backtest":
            print("Running Backtest...")
        else:
            print("Running Realtime Session until %s" % self.end_session_time)

        while self._continue_loop_condition():
            try:
                event = self.events_queue.get(False)
            except queue.Empty:
                self.price_handler.stream_next()
            else:
                if event is not None:
                    if (
                        event.type == EventType.TICK or
                        event.type == EventType.BAR
                    ):
                        self.cur_time = event.time
                        # Generate any sentiment events here
                        if self.sentiment_handler is not None:
                            self.sentiment_handler.stream_next(
                                stream_date=self.cur_time
                            )
                        self.strategy.calculate_signals(event)
                        self.portfolio_handler.update_portfolio_value()
                        self.statistics.update(event.time, self.portfolio_handler)
                    elif event.type == EventType.SENTIMENT:
                        self.strategy.calculate_signals(event)
                    elif event.type == EventType.SIGNAL:
                        self.portfolio_handler.on_signal(event)
                    elif event.type == EventType.ORDER:
                        self.execution_handler.execute_order(event)
                    elif event.type == EventType.FILL:
                        self.portfolio_handler.on_fill(event)
                    else:
                        raise NotImplementedError("Unsupported event.type '%s'" % event.type)

    def start_trading(self, testing=False):
        """
        Esegue un backtest o una sessione dal vivo e genera le prestazioni al termine.
        """
        self._run_session()
        results = self.statistics.get_results()
        print("---------------------------------")
        print("Backtest complete.")
        print("Sharpe Ratio: %0.2f" % results["sharpe"])
        print(
            "Max Drawdown: %0.2f%%" % (
                results["max_drawdown_pct"] * 100.0
            )
        )
        if not testing:
            self.statistics.plot_results()
        return results
