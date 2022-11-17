import os

import pandas as pd

from ..price_parser import PriceParser
from .base import AbstractBarPriceHandler
from ..event import BarEvent


class YahooDailyCsvBarPriceHandler(AbstractBarPriceHandler):
    """
    YahooDailyBarPriceHandler è progettato per leggere i file CSV
    dei dati giornalieri Open-High-Low-Close-Volume (OHLCV) di
    Yahoo Finance per ogni strumento finanziario richiesto
     e trasmetterli alla coda degli eventi come BarEvents.
    """
    def __init__(
        self, csv_dir, events_queue,
        init_tickers=None,
        start_date=None, end_date=None,
        calc_adj_returns=False
    ):
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
        self.start_date = start_date
        self.end_date = end_date
        self.bar_stream = self._merge_sort_ticker_data()
        self.calc_adj_returns = calc_adj_returns
        if self.calc_adj_returns:
            self.adj_close_returns = []

    def _open_ticker_price_csv(self, ticker):
        """
        Apre i file CSV contenenti i tick delle azioni dalla
        directory dei dati CSV specificata, convertendoli in
        un Pandas DataFrame, memorizzato in un dizionario.
        """
        ticker_path = os.path.join(self.csv_dir, "%s.csv" % ticker)
        self.tickers_data[ticker] = pd.io.parsers.read_csv(
            ticker_path, parse_dates=True, index_col=0
        )
        self.tickers_data[ticker]["Ticker"] = ticker

    def _merge_sort_ticker_data(self):
        """
        Concatena tutti i diversi DataFrame di azioni in un singolo
        DataFrame ordinato nel tempo, consentendo di aggiungere eventi
        di dati tick alla coda in modo cronologico.

        Nota: questa è una situazione idealizzata, utilizzata
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

        # Questo viene aggiunto in modo che gli eventi
        # ticker siano sempre deterministici, altrimenti
        # i valori degli unit test saranno diversi
        df['colFromIndex'] = df.index
        df = df.sort_values(by=["colFromIndex", "Ticker"])
        if start is None and end is None:
            return df.iterrows()
        elif start is not None and end is None:
            return df.iloc[start:].iterrows()
        elif start is None and end is not None:
            return df.iloc[:end].iterrows()
        else:
            return df.iloc[start:end].iterrows()

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
                adj_close = PriceParser.parse(row0["Adj Close"])

                ticker_prices = {
                    "close": close,
                    "adj_close": adj_close,
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
        Ottiene tutti gli elementi della barra da una riga
        di dataframe e restituisce un BarEvent
        """
        open_price = PriceParser.parse(row["Open"])
        high_price = PriceParser.parse(row["High"])
        low_price = PriceParser.parse(row["Low"])
        close_price = PriceParser.parse(row["Close"])
        adj_close_price = PriceParser.parse(row["Adj Close"])
        volume = int(row["Volume"])
        bev = BarEvent(
            ticker, index, period, open_price,
            high_price, low_price, close_price,
            volume, adj_close_price
        )
        return bev

    def _store_event(self, event):
        """
        Memorizza il prezzo di chiusura e di chiusura aggiustata per ogni evento
        """
        ticker = event.ticker
        # Se il flag calc_adj_returns è True, calcola e memorizza
        # in un elenco tutta la lista dei rendimenti percentuali
        # del prezzo di chiusura aggiustata
        # TODO: Aumentare la velocità
        if self.calc_adj_returns:
            prev_adj_close = self.tickers[ticker]["adj_close"] / float(PriceParser.PRICE_MULTIPLIER)
            cur_adj_close = event.adj_close_price / float(PriceParser.PRICE_MULTIPLIER)
            self.tickers[ticker][
                "adj_close_ret"
            ] = cur_adj_close / prev_adj_close - 1.0
            self.adj_close_returns.append(self.tickers[ticker]["adj_close_ret"])
        self.tickers[ticker]["close"] = event.close_price
        self.tickers[ticker]["adj_close"] = event.adj_close_price
        self.tickers[ticker]["timestamp"] = event.time

    def stream_next(self):
        """
        Posiziona il prossimo BarEvent nella coda degli eventi.
        """
        try:
            index, row = next(self.bar_stream)
        except StopIteration:
            self.continue_backtest = False
            return
        # Ottiene tutti gli elementi della barra dal dataframe
        ticker = row["Ticker"]
        period = 86400  # Seconds in a day
        # Crea un tick event per la coda
        bev = self._create_event(index, period, ticker, row)
        # Memorizza l'evento
        self._store_event(bev)
        # Invia l'evento alla coda
        self.events_queue.put(bev)
