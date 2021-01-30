from __future__ import print_function

from enum import Enum


EventType = Enum("EventType", "TICK BAR SIGNAL ORDER FILL SENTIMENT")


class Event(object):
    """
    Event è la classe base che fornisce un'interfaccia per tutti
    i successivi eventi (ereditati), che attiveranno ulteriori
    eventi nell'infrastruttura di trading.
    """
    @property
    def typename(self):
        return self.type.name


class TickEvent(Event):
    """
    Gestisce l'evento di ricezione di un nuovo tick di
    aggiornamento del mercato, che è definito come un simbolo
    ticker e la migliore offerta e domanda associate alla
    parte superiore del libro degli ordini.
    """
    def __init__(self, ticker, time, bid, ask):
        """
        Inizializza il TickEvent.

        Parametri:
        ticker - Il simbolo del ticker, ad es. "GOOG".
        time - Il timestamp del tick
        bid - Il miglior prezzo di offerta al momento del tick.
        ask - Il miglior prezzo ask al momento del tick.
        """
        self.type = EventType.TICK
        self.ticker = ticker
        self.time = time
        self.bid = bid
        self.ask = ask

    def __str__(self):
        return "Type: %s, Ticker: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.ticker),
            str(self.time), str(self.bid), str(self.ask)
        )

    def __repr__(self):
        return str(self)


class BarEvent(Event):
    """
    Gestisce l'evento di ricezione di una nuova barra
    OHLCV del mercato, come sarebbe generato tramite
    fornitori di dati comuni come Yahoo Finance.
    """
    def __init__(
        self, ticker, time, period,
        open_price, high_price, low_price,
        close_price, volume, adj_close_price=None
    ):
        """
        Inizializza il BarEvent.

        Parametri:
        ticker - Il simbolo del ticker, ad es. "GOOG".
        time - Il timestamp della barra
        period - Il periodo di tempo coperto dalla barra in secondi
        open_price - Il prezzo di apertura non aggiustato del bar
        high_price - Il prezzo elevato non aggiustato del bar
        low_price - Il prezzo basso non aggiustato del bar
        close_price - Il prezzo di chiusura non aggiustato della barra
        volume - Il volume degli scambi all'interno della barra
        adj_close_price - Il prezzo di chiusura rettificato del fornitore
            (es. regolazione all'indietro) della barra

        Nota: non è consigliabile utilizzare invece "open", "close"
        di "open_price", "close_price" come "open" è riservato
        parola in Python.

        """
        self.type = EventType.BAR
        self.ticker = ticker
        self.time = time
        self.period = period
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.adj_close_price = adj_close_price
        self.period_readable = self._readable_period()

    def _readable_period(self):
        """
        Crea un periodo leggibile dall'uomo a partire
        dal numero di secondi specificato per "period".

        Ad esempio, converte:
        * 1 -> "1 sec"
        * 5 -> "5 sec"
        * 60 -> "1 min"
        * 300 -> "5 min"

        Se non viene trovato alcun punto nella tabella di ricerca,
        il periodo leggibile dall'uomo viene semplicemente
        passato dal punto, in secondi.
        """
        lut = {
            1: "1sec",
            5: "5sec",
            10: "10sec",
            15: "15sec",
            30: "30sec",
            60: "1min",
            300: "5min",
            600: "10min",
            900: "15min",
            1800: "30min",
            3600: "1hr",
            86400: "1day",
            604800: "1wk"
        }
        if self.period in lut:
            return lut[self.period]
        else:
            return "%ssec" % str(self.period)

    def __str__(self):
        format_str = "Type: %s, Ticker: %s, Time: %s, Period: %s, " \
            "Open: %s, High: %s, Low: %s, Close: %s, " \
            "Adj Close: %s, Volume: %s" % (
                str(self.type), str(self.ticker), str(self.time),
                str(self.period_readable), str(self.open_price),
                str(self.high_price), str(self.low_price),
                str(self.close_price), str(self.adj_close_price),
                str(self.volume)
            )
        return format_str

    def __repr__(self):
        return str(self)


class SignalEvent(Event):
    """
    Gestisce l'evento di invio di un segnale da un oggetto strategia.
    Questo viene ricevuto da un oggetto Portfolio e su cui si agisce.
    """
    def __init__(self, ticker, action, suggested_quantity=None):
        """
        Inizializza il SignalEvent.

        Parametri:
        ticker - Il simbolo del ticker, ad es. "GOOG".
        action - "BOT" (per i long) o "SLD" (per gli short).
        suggested_quantity: numero intero facoltativo con valore
            positivo che rappresenta una quantità assoluta suggerita
            di unità di un asset in cui eseguire la transazione,
            utilizzato da PositionSizer e RiskManager.
        """
        self.type = EventType.SIGNAL
        self.ticker = ticker
        self.action = action
        self.suggested_quantity = suggested_quantity


class OrderEvent(Event):
    """
    Gestisce l'evento di invio di un ordine a un sistema di esecuzione.
    L'ordine contiene un ticker (ad esempio GOOG), un'azione (BOT o SLD) e una quantità.
    """
    def __init__(self, ticker, action, quantity):
        """
        Inizializza l'OrderEvent.

        Parametri:
        ticker - Il simbolo del ticker, ad es. "GOOG".
        action - "BOT" (per i long) o "SLD" (per gli short).
        quantity: la quantità di azioni da negoziare.
        """
        self.type = EventType.ORDER
        self.ticker = ticker
        self.action = action
        self.quantity = quantity

    def print_order(self):
        """
        Stampa dei valori che compongono l'OrderEvent.
        """
        print(
            "Order: Ticker=%s, Action=%s, Quantity=%s" % (
                self.ticker, self.action, self.quantity
            )
        )


class FillEvent(Event):
    """
    Incapsula la nozione di un ordine eseguito, come restituito
    da un trade. Memorizza la quantità di uno strumento
    effettivamente eseguita e a quale prezzo. Inoltre,
    memorizza la commissione applicata dal broker.

    TODO: Attualmente non supporta posizioni di riempimento
    a prezzi diversi. Questo verrà simulato calcolando la media.
    """

    def __init__(
        self, timestamp, ticker,
        action, quantity,
        exchange, price,
        commission
    ):
        """
        Inizializza l'oggetto FillEvent.

        timestamp - Il timestamp in cui l'ordine è stato eseguito.
        ticker - Il simbolo del ticker, ad es. "GOOG".
        action - "BOT" (per i long) o "SLD" (per gli short).
        quantity - La quantità eseguita.
        exchange - il broker in cui è stato eseguito l'ordine.
        price - Il prezzo a cui è stata eseguita la transazione
        commission - La commissione del broker per lo svolgimento della transazione.

        """
        self.type = EventType.FILL
        self.timestamp = timestamp
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
        self.exchange = exchange
        self.price = price
        self.commission = commission


class SentimentEvent(Event):
    """
    Gestisce l'evento di streaming di un valore "Sentiment" associato
    a un ticker. Può essere utilizzato per un servizio generico
    "data-ticker-sentiment", spesso fornito da molti fornitori di dati.
    """
    def __init__(self, timestamp, ticker, sentiment):
        """
        Inizializza il SentimentEvent.

        Parameters:
        timestamp - il timestamp in cui l'ordine è stato eseguito.
        ticker - Il simbolo del ticker, ad es. "GOOG".
        sentiment - Una stringa, un valore float o un valore intero
            di "sentiment", ad es. "rialzista", -1, 5.4, ecc.
        """
        self.type = EventType.SENTIMENT
        self.timestamp = timestamp
        self.ticker = ticker
        self.sentiment = sentiment
