import os

import pandas as pd

from ..price_parser import PriceParser
from .base import AbstractBarPriceHandler
from ..event import BarEvent


class IQFeedIntradayCsvBarPriceHandler(AbstractBarPriceHandler):
    """
    IQFeedIntradayCsvBarPriceHandler è progettato per leggere
    i file CSV delle barre intraday scaricati da DTN IQFeed,
    costituiti da dati Open-Low-High-Close-Volume-OpenInterest
    (OHLCVI) per ogni strumento finanziario richiesto e
    trasmetterli alla coda degli eventi fornita come BarEvents.
    """
    def __init__(
        self, csv_dir, events_queue,
        init_tickers=None,
        start_date=None, end_date=None
    ):
        """
        Prende la directory CSV, la coda degli eventi e un possibile
        elenco di simboli ticker iniziali, quindi crea un elenco
        (opzionale) di sottoscrizioni di ticker e prezzi associati.
        """
        self.csv_dir = csv_dir
        self.events_queue = events_queue
        self.continue_backtest = True
        self.tickers = {}
        self.tickers_data = {}
        if init_tickers is not None:
            for ticker in init_tickers:
                self.subscribe_ticker(ticker)
        self.start_date = start_date
        self.end_date = end_date
        self.bar_stream = self._merge_sort_ticker_data()

    def _open_ticker_price_csv(self, ticker):
        """
        Apre i file CSV contenenti i tick delle azioni dalla
        directory dei dati CSV specificata, convertendoli
        in un DataFrame panda, memorizzato in un dizionario.
        """
        ticker_path = os.path.join(self.csv_dir, "%s.csv" % ticker)

        self.tickers_data[ticker] = pd.read_csv(
            ticker_path,
            names=[
                "Date", "Open", "Low", "High",
                "Close", "Volume", "OpenInterest"
            ],
            index_col="Date", parse_dates=True
        )
        self.tickers_data[ticker]["Ticker"] = ticker

    def _merge_sort_ticker_data(self):
        """
        Concatena tutti i diversi DataFrame di azioni in un singolo
        DataFrame ordinato nel tempo, consentendo di aggiungere eventi
        di dati tick alla coda in modo cronologico.

        Nota che questa è una situazione idealizzata, utilizzata
        esclusivamente per il backtest. Nel trading live i tick
        possono arrivare "fuori servizio".
        """
        df = pd.concat(self.tickers_data.values()).sort_index()
        start = None
        end = None
        if self.start_date is not None:
            start = df.index.searchsorted(self.start_date)
        if self.end_date is not None:
            end = df.index.searchsorted(self.end_date)
        # Determina come fare lo spostamento
        if start is None and end is None:
            return df.iterrows()
        elif start is not None and end is None:
            return df.ix[start:].iterrows()
        elif start is None and end is not None:
            return df.ix[:end].iterrows()
        else:
            return df.ix[start:end].iterrows()

    def subscribe_ticker(self, ticker):
        """
        Sottoscrive il gestore del prezzo a un nuovo simbolo ticker.
        """
        if ticker not in self.tickers:
            try:
                self._open_ticker_price_csv(ticker)
                dft = self.tickers_data[ticker]
                row0 = dft.iloc[0]

                close = PriceParser.parse(row0["Close"])

                ticker_prices = {
                    "close": close,
                    "adj_close": close,
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

    def _create_event(self, index, period, ticker, row):
        """
        Ottiene tutti gli elementi della barra da una riga di
        dataframe e restituisce un BarEvent
        """
        open_price = PriceParser.parse(row["Open"])
        low_price = PriceParser.parse(row["Low"])
        high_price = PriceParser.parse(row["High"])
        close_price = PriceParser.parse(row["Close"])
        adj_close_price = PriceParser.parse(row["Close"])
        volume = int(row["Volume"])
        bev = BarEvent(
            ticker, index, period, open_price,
            high_price, low_price, close_price,
            volume, adj_close_price
        )
        return bev

    def stream_next(self):
        """
        Inserire il prossimo BarEvent nella coda degli eventi.
        """
        try:
            index, row = next(self.bar_stream)
        except StopIteration:
            self.continue_backtest = False
            return
        # Ottieni tutti gli elementi della barra dal dataframe
        ticker = row["Ticker"]
        period = 60  # Secondi un minuto
        # Crea l'evento tick per la coda
        bev = self._create_event(index, period, ticker, row)
        # Memorizza l'evento
        self._store_event(bev)
        # Invia l'evento alla coda
        self.events_queue.put(bev)
