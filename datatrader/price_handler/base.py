from __future__ import print_function

from abc import ABCMeta


class AbstractPriceHandler(object):
    """
    PriceHandler è una classe base che fornisce un'interfaccia per
    tutti i gestori di dati successivi (ereditati) (sia live che storici).

    L'obiettivo di un oggetto PriceHandler (derivato) è quello di produrre
    una serie di TickEvents o BarEvents per ogni strumento finanziario
    e di inserirli in una coda di eventi.

    Questo replicherà il modo in cui una strategia live funzionerebbe poiché
    i dati correnti di tick / bar sarebbero trasmessi in streaming tramite un
    broker o feed di dati. Quindi un sistema storico e live verrà trattato
    in modo identico dal resto della suite DataTrader.
    """

    __metaclass__ = ABCMeta

    def unsubscribe_ticker(self, ticker):
        """
        Annulla la sottoscrizione al gestore del prezzo da un simbolo ticker corrente.
        """
        try:
            self.tickers.pop(ticker, None)
            self.tickers_data.pop(ticker, None)
        except KeyError:
            print(
                "Could not unsubscribe ticker %s "
                "as it was never subscribed." % ticker
            )

    def get_last_timestamp(self, ticker):
        """
        Restituisce il timestamp effettivo più recente per un dato ticker
        """
        if ticker in self.tickers:
            timestamp = self.tickers[ticker]["timestamp"]
            return timestamp
        else:
            print(
                "Timestamp for ticker %s is not "
                "available from the %s." % (ticker, self.__class__.__name__)
            )
            return None


class AbstractTickPriceHandler(AbstractPriceHandler):
    def istick(self):
        return True

    def isbar(self):
        return False

    def _store_event(self, event):
        """
        Memorizza il prezzo bid/ask dell'evento
        """
        ticker = event.ticker
        self.tickers[ticker]["bid"] = event.bid
        self.tickers[ticker]["ask"] = event.ask
        self.tickers[ticker]["timestamp"] = event.time

    def get_best_bid_ask(self, ticker):
        """
        Restituisce il prezzo bid / ask più recente per un ticker.
        """
        if ticker in self.tickers:
            bid = self.tickers[ticker]["bid"]
            ask = self.tickers[ticker]["ask"]
            return bid, ask
        else:
            print(
                "Bid/ask values for ticker %s are not "
                "available from the PriceHandler." % ticker
            )
            return None, None


class AbstractBarPriceHandler(AbstractPriceHandler):
    def istick(self):
        return False

    def isbar(self):
        return True

    def _store_event(self, event):
        """
        Memorizza il prezzo di chiusura e chiusura aggiustata dell'evento
        """
        ticker = event.ticker
        self.tickers[ticker]["close"] = event.close_price
        self.tickers[ticker]["adj_close"] = event.adj_close_price
        self.tickers[ticker]["timestamp"] = event.time

    def get_last_close(self, ticker):
        """
        Restituisce il prezzo di chiusura effettivo (non corretto) più recente
        """
        if ticker in self.tickers:
            close_price = self.tickers[ticker]["close"]
            return close_price
        else:
            print(
                "Close price for ticker %s is not "
                "available from the YahooDailyBarPriceHandler."
            )
            return None
