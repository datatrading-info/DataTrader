from .base import AbstractExecutionHandler
from ..event import (FillEvent, EventType)
from ..price_parser import PriceParser


class IBSimulatedExecutionHandler(AbstractExecutionHandler):
    """
    Il gestore di esecuzione simulato per Interactive Brokers
    converte automaticamente tutti gli oggetti Order nei loro
    equivalenti oggetti Fill senza problemi di latenza, slippage
    o rapporto di riempimento.

    Ciò consente un semplice test "first go" di qualsiasi strategia,
    prima dell'implementazione con un gestore di esecuzione più sofisticato.
    """

    def __init__(self, events_queue, price_handler, compliance=None):
        """
        Inizializza il gestore, impostando la coda degli eventi
        e l'accesso ai prezzi locali.

        Parametri:
        events_queue - La coda degli oggetti Event.
        """
        self.events_queue = events_queue
        self.price_handler = price_handler
        self.compliance = compliance

    def calculate_ib_commission(self, quantity, fill_price):
        """
        Calcola la commissione di Interactive Brokers per una transazione.
        Questo si basa sui prezzi fissi degli Stati Uniti, i cui dettagli
        sono disponibili qui:
        https://www.interactivebrokers.co.uk/en/index.php?f=1590&p=stocks1
        """
        commission = min(
            0.5 * fill_price * quantity,
            max(1.0, 0.005 * quantity)
        )
        return PriceParser.parse(commission)

    def execute_order(self, event):
        """
        Converte OrderEvents in FillEvents "ingenuamente", ovvero senza
        problemi di latenza, slittamento o rapporto di riempimento.

        Parametri:
        event - Un oggetto Event con informazioni sull'ordine.
        """
        if event.type == EventType.ORDER:
            # Ottenere valori dall'OrderEvent
            timestamp = self.price_handler.get_last_timestamp(event.ticker)
            ticker = event.ticker
            action = event.action
            quantity = event.quantity

            # Ottenere il prezzo di esecuzione
            if self.price_handler.istick():
                bid, ask = self.price_handler.get_best_bid_ask(ticker)
                if event.action == "BOT":
                    fill_price = ask
                else:
                    fill_price = bid
            else:
                close_price = self.price_handler.get_last_close(ticker)
                fill_price = close_price

            # Imposta uno exchange fittizio e calcola la commissione dei trade
            exchange = "ARCA"
            commission = self.calculate_ib_commission(quantity, fill_price)

            # Crea il FillEvent e lo posiziona nella coda degli eventi
            fill_event = FillEvent(
                timestamp, ticker,
                action, quantity,
                exchange, fill_price,
                commission
            )
            self.events_queue.put(fill_event)

            if self.compliance is not None:
                self.compliance.record_trade(fill_event)
