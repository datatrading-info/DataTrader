from __future__ import print_function

from abc import ABCMeta


class AbstractSentimentHandler(object):
    """
    AbstractSentimentHandler è una classe base astratta che fornisce
    un'interfaccia per tutti i gestori di eventi di analisi del sentiment ereditati.

    Il suo obiettivo è consentire la creazione di sottoclassi per oggetti che
    leggono dati di sentiment basati su file (come file CSV di tuple data-asset-sentiment)
    o dati di sentiment in streaming da un'API e produce un output basato su eventi
    che invia oggetti SentimentEvent alla coda degli eventi.
    """

    __metaclass__ = ABCMeta

    def stream_next(self, stream_date=None):
        """
        Metodo di interfaccia per lo streaming del successivo
        oggetto SentimentEvent nella coda degli eventi.
        """
        raise NotImplementedError("stream_next is not implemented in the base class!")
