from abc import ABCMeta, abstractmethod


class AbstractPositionSizer(object):
    """
    La classe astratta AbstractPositionSizer modifica
    la quantità (o meno) di qualsiasi azione negoziata
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def size_order(self, portfolio, initial_order):
        """
        Questo oggetto TestPositionSizer modifica
        semplicemente la quantità in modo che sia 100
        per qualsiasi azione negoziata.
        """
        raise NotImplementedError("Should implement size_order()")
