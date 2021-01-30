from ..base import AbstractTickEventIterator


class PandasDataFrameTickEventIterator(AbstractTickEventIterator):
    """
    PandasPanelBarEventIterator è progettato per leggere Pandas DataFrame del tipo

                                   Bid        Ask
    Time
    2016-02-01 00:00:01.358  683.56000  683.58000
    2016-02-01 00:00:02.544  683.55998  683.58002
    2016-02-01 00:00:03.765  683.55999  683.58001
    ...
    2016-02-01 00:00:10.823  683.56001  683.57999
    2016-02-01 00:00:12.221  683.56000  683.58000
    2016-02-01 00:00:13.546  683.56000  683.58000

    con tick data (bid/ask)
    per ogni strumento finanzario ed ogni ickEvents elaborato
    """
    def __init__(self, df, ticker):
        """
        Accetta la coda degli eventi, il ticker e Pandas DataFrame
        """
        self.data = df
        self.ticker = ticker
        self.tickers_lst = [ticker]
        self._itr_bar = self.data.iterrows()

    def __next__(self):
        index, row = next(self._itr_bar)
        price_event = self._create_event(index, self.ticker, row)
        return price_event


class PandasPanelTickEventIterator(AbstractTickEventIterator):
    """
    PandasPanelBarEventIterator è progettato per leggere Pandas Panel come

    <class 'pandas.core.panel.Panel'>
    Dimensions: 2 (items) x 20 (major_axis) x 2 (minor_axis)
    Items axis: Bid to Ask
    Major_axis axis: 2016-02-01 00:00:01.358000 to 2016-02-01 00:00:14.153000
    Minor_axis axis: GOOG to MSFT

    con tick data (bid/ask)
    per ogni strumento finanzario ed ogni TickEvents elaborato
    """
    def __init__(self, panel):
        self.data = panel
        self._itr_ticker_bar = self.data.transpose(1, 0, 2).iteritems()
        self.tickers_lst = self.data.minor_axis
        self._next_ticker_bar()

    def _next_ticker_bar(self):
        self.index, self.df = next(self._itr_ticker_bar)
        self._itr_bar = self.df.iteritems()

    def __next__(self):
        try:
            ticker, row = next(self._itr_bar)
        except StopIteration:
            self._next_ticker_bar()
            ticker, row = next(self._itr_bar)
        bev = self._create_event(self.index, ticker, row)
        return bev


def PandasTickEventIterator(data, ticker=None):
    """
    PandasTickEventIterator restituisce un iteratore di prezzo
    progettato per leggere un Pandas DataFrame (o un Pandas Panel)
    con tick data (bid/ask)
    per ogni strumento finanzario ed ogni TickEvents elaborato
    """
    if hasattr(data, 'minor_axis'):
        return PandasPanelTickEventIterator(data)
    else:
        return PandasDataFrameTickEventIterator(data, ticker)
