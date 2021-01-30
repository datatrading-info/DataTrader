from abc import ABCMeta, abstractmethod

from ..compat import pickle


class AbstractStatistics(object):
    """
    Statistics è una classe astratta che fornisce un'interfaccia per tutte
    le classi di statistiche ereditate (live, storiche, personalizzate, ecc.).

    L'obiettivo di un oggetto Statistics è quello di tenere traccia delle informazioni
    relative ad una o più strategie di trading mentre la strategia è in esecuzione.
    Questo viene fatto collegandosi al ciclo principale degli eventi e essenzialmente
    aggiornando l'oggetto in base alle prestazioni del portafoglio nel tempo.

    Idealmente, questa classe deve essere eridata da sottoclassi specifiche in base
    alle strategie e ai timeframe utilizzati. Strategie di trading diverse possono
    richiedere l'aggiornamento di metriche diverse o diverse frequenze-di-metriche,
    tuttavia l'esempio fornito è adatto per i timeframe più lunghi.

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update(self):
        """
        Aggiorna tutte le statistiche in base ai valori del portafoglio
        e delle posizioni aperte. Questo dovrebbe essere chiamato
        all'interno del ciclo di eventi.
        """
        raise NotImplementedError("Should implement update()")

    @abstractmethod
    def get_results(self):
        """
        Restituisce un dizionario contenenti tutte le statistiche.
        """
        raise NotImplementedError("Should implement get_results()")

    @abstractmethod
    def plot_results(self):
        """
        Stampa i grafici delle statistiche memorizzate fino ad "ora".
        """
        raise NotImplementedError("Should implement plot_results()")

    @abstractmethod
    def save(self, filename):
        """
        Memorizza i risultati delle statistiche in un file.
        """
        raise NotImplementedError("Should implement save()")

    @classmethod
    def load(cls, filename):
        with open(filename, 'rb') as fd:
            stats = pickle.load(fd)
        return stats


def load(filename):
    return AbstractStatistics.load(filename)
