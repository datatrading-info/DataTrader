from abc import ABCMeta, abstractmethod


class AbstractExecutionHandler(object):
    """
    La classe astratta ExecutionHandler gestisce l'interazione tra un
    insieme di oggetti 'Order' generati da un PortfolioHandler e
    l'insieme di oggetti 'Fill' che si verificano effettivamente nel mercato.

    I gestori possono essere utilizzati per sottoclassare broker simulati
    o live broker, con interfacce identiche. Ciò consente di eseguire il
    backtest delle strategie in modo molto simile al motore di trading live.

    ExecutionHandler può collegarsi a un componente Compliance opzionale
    per una semplice registrazione dei dati, che terrà traccia di
    tutti gli ordini eseguiti.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event):
        """
        Prende un OrderEvent e lo esegue, producendo un FillEvent che v
        iene inserito nella coda degli eventi.

        Parametri:
        event - Contiene un oggetto Event con informazioni sull'ordine.
        """
        raise NotImplementedError("Should implement execute_order()")

    @abstractmethod
    def cancel_order(self, order_id):
        """"""
        raise NotImplementedError("Implement this in your derived class")

    @abstractmethod
    def next_order_id(self):
        """"""
        raise NotImplementedError("Implement this in your derived class")

    @abstractmethod
    def _calculate_commission(self, fill_symbol, fill_price, fill_size):
        """"""
        raise NotImplementedError("Implement this in your derived class")
