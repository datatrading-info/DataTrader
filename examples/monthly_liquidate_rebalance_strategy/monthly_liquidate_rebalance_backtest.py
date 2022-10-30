import datetime
import calendar

from datatrader import settings
from datatrader.position_sizer.rebalance import LiquidateRebalancePositionSizer
from datatrader.compat import queue
from datatrader.trading_session import TradingSession

from datatrader.strategy.base import AbstractStrategy
from datatrader.event import SignalEvent, EventType


class MonthlyLiquidateRebalanceStrategy(AbstractStrategy):
    """
    Una strategia generica che consente il ribilanciamento mensile di
    una serie di ticker, tramite la piena liquidazione e la pesatura
    in dollari delle nuove posizioni.

    Per funzionare correttamente deve essere utilizzato insieme
    all'oggetto LiquidateRebalancePositionSizer.
    """
    def __init__(self, tickers, events_queue):
        self.tickers = tickers
        self.events_queue = events_queue
        self.tickers_invested = self._create_invested_list()

    def _end_of_month(self, cur_time):
        """
        Determina se il giorno corrente è alla fine del mese.
        """
        cur_day = cur_time.day
        end_day = calendar.monthrange(cur_time.year, cur_time.month)[1]
        return cur_day == end_day

    def _create_invested_list(self):
        """
        Crea un dizionario con ogni ticker come chiave, con un valore
        booleano a seconda che il ticker sia stato ancora "investito".
        Ciò è necessario per evitare di inviare un segnale di
        liquidazione sulla prima allocazione.
        """
        tickers_invested = {ticker: False for ticker in self.tickers}
        return tickers_invested

    def calculate_signals(self, event):
        """
        Per uno specifico BarEvent ricevuto, determina se è la fine del
        mese (per quella barra) e genera un segnale di liquidazione,
        oltre a un segnale di acquisto, per ogni ticker.
        """
        if (
            event.type in [EventType.BAR, EventType.TICK] and
            self._end_of_month(event.time)
        ):
            ticker = event.ticker
            if self.tickers_invested[ticker]:
                liquidate_signal = SignalEvent(ticker, "EXIT")
                self.events_queue.put(liquidate_signal)
            long_signal = SignalEvent(ticker, "BOT")
            self.events_queue.put(long_signal)
            self.tickers_invested[ticker] = True


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
