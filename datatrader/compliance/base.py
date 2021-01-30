from abc import ABCMeta, abstractmethod


class AbstractCompliance(object):
    """
    La componente Compliance dovrebbe essere assegnata
    a ogni operazione che avviene in datatrader.

    È progettato per tenere traccia di tutto ciò che
    potrebbe essere richiesto per scopi normativi o
    di controllo (o debug).
    Le versioni estese possono scrivere operazioni
    su un CSV o su un database.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def record_trade(self, fill):
        """
        Prende un FillEvent da un ExecutionHandler e
        registra ciascuno di questi.

        Parametri:
        fill - Un FillEvent con informazioni sulla
            transazione che è stata appena eseguita.
        """
        raise NotImplementedError("Should implement record_trade()")
