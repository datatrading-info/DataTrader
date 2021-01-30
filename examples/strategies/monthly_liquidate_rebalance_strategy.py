import calendar

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

