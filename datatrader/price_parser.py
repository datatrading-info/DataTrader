from __future__ import division
from multipledispatch import dispatch
import numpy as np

int_t = (int, np.int64)


class PriceParser(object):
    """
    PriceParser è progettato per astrarre il numero sottostante utilizzato
    come prezzo all'interno di DataTrader. A causa dei limiti di efficienza
    e precisione dei dati in virgola mobile, DataTrader utilizza un numero
    intero per rappresentare tutti i prezzi. Ciò significa che $0,10 è,
    internamente, rappresentato come 10.000.000. Poiché numeri così grandi
    sono difficili da utilizzare per gli umani, PriceParser prenderà come
    input numeri 2dp "normali" e mostrerà numeri 2dp "normali" come output
    quando richiesto la stampa a video

    Per motivi di coerenza, PriceParser dovrebbe essere utilizzato per TUTTI
    i prezzi che entrano nel sistema DataTrader. Anche i numeri devono essere
    sempre analizzati correttamente per essere visualizzati.
    """

    # 10,000,000
    PRICE_MULTIPLIER = 10000000

    """Metodi di analisi. Moltiplica un float in un int, se necessario."""

    @staticmethod
    @dispatch(int_t)
    def parse(x):  # flake8: noqa
        return x

    @staticmethod
    @dispatch(str)
    def parse(x):  # flake8: noqa
        return int(float(x) * PriceParser.PRICE_MULTIPLIER)

    @staticmethod
    @dispatch(float)
    def parse(x):  # flake8: noqa
        return int(x * PriceParser.PRICE_MULTIPLIER)

    """Metodi di visualizzazione. Moltiplica un float in un int, se necessario. """

    @staticmethod
    @dispatch(int_t)
    def display(x):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, 2)

    @staticmethod
    @dispatch(float)
    def display(x):  # flake8: noqa
        return round(x, 2)

    @staticmethod
    @dispatch(int_t, int)
    def display(x, dp):  # flake8: noqa
        return round(x / PriceParser.PRICE_MULTIPLIER, dp)

    @staticmethod
    @dispatch(float, int)
    def display(x, dp):  # flake8: noqa
        return round(x, dp)
