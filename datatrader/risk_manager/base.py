from abc import ABCMeta, abstractmethod


class AbstractRiskManager(object):
    """
    La classe astratta AbstractRiskManager lascia passare
    l'ordine dimensionato, crea l'oggetto OrderEvent
    corrispondente e lo aggiunge alla coda.
    """

    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    @abstractmethod
    def refine_orders(self, portfolio, sized_order):
        raise NotImplementedError("Should implement refine_orders()")
