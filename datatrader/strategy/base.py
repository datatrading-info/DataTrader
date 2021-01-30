from abc import ABCMeta, abstractmethod


class AbstractStrategy(object):
    """
    AbstractStrategy è una classe base astratta che fornisce un'interfaccia
    per tutti i successivi oggetti di gestione della strategia (ereditati).

    L'obiettivo di un oggetto Strategy (derivato) è generare oggetti Signal
    per specifici simboli basati sugli input di tick generati da un oggetto
    PriceHandler (derivato).

    Questo è progettato per funzionare sia con i dati storici che con quelli
    in tempo reale poiché l'oggetto Strategy è indipendente dalla sorgente dei dati.

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self, event):
        """
        Fornisce i meccanismi per calcolare l'elenco dei segnali.
        """
        raise NotImplementedError("Should implement calculate_signals()")


class Strategies(AbstractStrategy):
    """
    Strategies è una collezione di strategie
    """
    def __init__(self, *strategies):
        self._lst_strategies = strategies

    def calculate_signals(self, event):
        for strategy in self._lst_strategies:
            strategy.calculate_signals(event)
