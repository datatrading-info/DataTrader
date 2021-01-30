from .base import AbstractRiskManager
from ..event import OrderEvent


class ExampleRiskManager(AbstractRiskManager):
    def refine_orders(self, portfolio, sized_order):
        """
        Questo oggetto ExampleRiskManager lascia passare
        semplicemente l'ordine dimensionato, crea l'oggetto
        OrderEvent corrispondente e lo aggiunge alla coda.
        """
        order_event = OrderEvent(
            sized_order.ticker,
            sized_order.action,
            sized_order.quantity
        )
        return [order_event]
