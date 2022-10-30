
from datatrader.event import (SignalEvent, EventType)
from datatrader.strategy.base import AbstractStrategy

class SentdexSentimentStrategy(AbstractStrategy):
    """
    Requisiti:
    tickers - La lista dei simboli dei ticker
    events_queue - La coda degli eventi
    sent_buy - soglia di entrata
    sent_sell - soglia di uscita
    base_quantity - Numero di azioni ogni azione
    """
    def __init__(
        self, tickers, events_queue,
        sent_buy, sent_sell, base_quantity
    ):
        self.tickers = tickers
        self.events_queue = events_queue
        self.sent_buy = sent_buy
        self.sent_sell = sent_sell
        self.qty = base_quantity
        self.time = None
        self.tickers.remove("SPY")
        self.invested = dict(
            (ticker, False) for ticker in self.tickers
        )

    def calculate_signals(self, event):
        """
        Calcola i segnali della strategia
        """
        if event.type == EventType.SENTIMENT:
            ticker = event.ticker
            # Segnale Long
            if (
                    self.invested[ticker] is False and
                    event.sentiment >= self.sent_buy
            ):
                print("LONG %s at %s" % (ticker, event.timestamp))
                self.events_queue.put(SignalEvent(ticker, "BOT", self.qty))
                self.invested[ticker] = True
            # Chiusura segnale
            if (
                    self.invested[ticker] is True and
                    event.sentiment <= self.sent_sell
            ):
                print("CLOSING LONG %s at %s" % (ticker, event.timestamp))
                self.events_queue.put(SignalEvent(ticker, "SLD", self.qty))
                self.invested[ticker] = False