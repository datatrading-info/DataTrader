from __future__ import print_function

import os

import pandas as pd

from .base import AbstractTickPriceHandler
from ..event import TickEvent
from ..price_parser import PriceParser


class HistoricCSVTickPriceHandler(AbstractTickPriceHandler):
    """
    HistoricCSVPriceHandler è progettato per leggere file CSV
    di dati tick per ogni strumento finanziario richiesto e
    trasmetterli alla coda degli eventi forniti come TickEvents.
    """
    def __init__(self, csv_dir, events_queue, init_tickers=None):
        """
        Prende la directory CSV, la coda degli eventi e un possibile
        elenco di simboli ticker iniziali, quindi crea un elenco
        (opzionale) di abbonamenti ticker e prezzi associati.
        """
        self.csv_dir = csv_dir
        self.events_queue = events_queue
        self.continue_backtest = True
        self.tickers = {}
        self.tickers_data = {}
        if init_tickers is not None:
            for ticker in init_tickers:
                self.subscribe_ticker(ticker)
        self.tick_stream = self._merge_sort_ticker_data()

    def _open_ticker_price_csv(self, ticker):
        """
        Apre i file CSV contenenti i tick delle azioni dalla
        directory dei dati CSV specificata, convertendoli in
        essi in un DataFrame panda, memorizzato in un dizionario.
        """
        ticker_path = os.path.join(self.csv_dir, "%s.csv" % ticker)
        self.tickers_data[ticker] = pd.io.parsers.read_csv(
            ticker_path, header=0, parse_dates=True,
            dayfirst=True, index_col=1,
            names=("Ticker", "Time", "Bid", "Ask")
        )

    def _merge_sort_ticker_data(self):
        """
        Concatena tutti i DataFrame di azioni separate in un unico
        DataFrame ordinato nel tempo, consentendo di aggiungere alla
        coda eventi di dati tick in modo cronologico.

        Nota che questa è una situazione idealizzata, utilizzata
        esclusivamente per il backtest. Nel trading live i tick
        possono arrivare "fuori servizio".
        """
        return pd.concat(
            self.tickers_data.values()
        ).sort_index().iterrows()

    def subscribe_ticker(self, ticker):
        """
        Sottoscrive il gestore del prezzo con un nuovo simbolo ticker.
        """
        if ticker not in self.tickers:
            try:
                self._open_ticker_price_csv(ticker)
                dft = self.tickers_data[ticker]
                row0 = dft.iloc[0]
                ticker_prices = {
                    "bid": PriceParser.parse(row0["Bid"]),
                    "ask": PriceParser.parse(row0["Ask"]),
                    "timestamp": dft.index[0]
                }
                self.tickers[ticker] = ticker_prices
            except OSError:
                print(
                    "Could not subscribe ticker %s "
                    "as no data CSV found for pricing." % ticker
                )
        else:
            print(
                "Could not subscribe ticker %s "
                "as is already subscribed." % ticker
            )

    def _create_event(self, index, ticker, row):
        """
        Ottiene tutti gli elementi della barra come riga
        di dataframe e restituisce un TickEvent
        """
        bid = PriceParser.parse(row["Bid"])
        ask = PriceParser.parse(row["Ask"])
        tev = TickEvent(ticker, index, bid, ask)
        return tev

    def stream_next(self):
        """
        Posiziona il successivo TickEvent nella coda degli eventi.
        """
        try:
            index, row = next(self.tick_stream)
        except StopIteration:
            self.continue_backtest = False
            return
        ticker = row["Ticker"]
        tev = self._create_event(index, ticker, row)
        self._store_event(tev)
        self.events_queue.put(tev)
