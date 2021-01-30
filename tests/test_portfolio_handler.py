import datetime
from decimal import Decimal
import unittest

from datatrader.event import FillEvent, OrderEvent, SignalEvent
from datatrader.portfolio_handler import PortfolioHandler
from datatrader.price_handler.base import AbstractTickPriceHandler
from datatrader.compat import queue


class PriceHandlerMock(AbstractTickPriceHandler):
    def __init__(self):
        pass

    def get_best_bid_ask(self, ticker):
        prices = {
            "MSFT": (Decimal("50.28"), Decimal("50.31")),
            "GOOG": (Decimal("705.46"), Decimal("705.46")),
            "AMZN": (Decimal("564.14"), Decimal("565.14")),
        }
        return prices[ticker]


class PositionSizerMock(object):
    def __init__(self):
        pass

    def size_order(self, portfolio, initial_order):
        """
        Questo oggetto PositionSizerMock modifica
        semplicemente la quantità in modo che sia 100
        per qualsiasi azione negoziata.
        """
        initial_order.quantity = 100
        return initial_order


class RiskManagerMock(object):
    def __init__(self):
        pass

    def refine_orders(self, portfolio, sized_order):
        """
        Questo oggetto RiskManagerMock lascia semplicemente
        passare l'ordine dimensionato, crea l'oggetto
        OrderEvent corrispondente e lo aggiunge alla coda.
        """
        order_event = OrderEvent(
            sized_order.ticker,
            sized_order.action,
            sized_order.quantity
        )
        return [order_event]


class TestSimpleSignalOrderFillCycleForPortfolioHandler(unittest.TestCase):
    """
    Verifica un semplice ciclo di segnale, ordine e
    riempimento per il PortfolioHandler. Questo è, in effetti,
    un controllo di integrità.
    """
    def setUp(self):
        """
        Imposta l'oggetto PortfolioHandler fornendogli
        $500.000,00 USD di contanti iniziale.
        """
        initial_cash = Decimal("500000.00")
        events_queue = queue.Queue()
        price_handler = PriceHandlerMock()
        position_sizer = PositionSizerMock()
        risk_manager = RiskManagerMock()
        # Crea l'oggetto PortfolioHandler
        self.portfolio_handler = PortfolioHandler(
            initial_cash, events_queue, price_handler,
            position_sizer, risk_manager
        )

    def test_create_order_from_signal_basic_check(self):
        """
        Verifica il metodo "_create_order_from_signal"
        come controllo di integrità di base.
        """
        signal_event = SignalEvent("MSFT", "BOT")
        order = self.portfolio_handler._create_order_from_signal(signal_event)
        self.assertEqual(order.ticker, "MSFT")
        self.assertEqual(order.action, "BOT")
        self.assertEqual(order.quantity, 0)

    def test_place_orders_onto_queue_basic_check(self):
        """
        Verifica il metodo "_place_orders_onto_queue"
        come controllo di integrità di base.
        """
        order = OrderEvent("MSFT", "BOT", 100)
        order_list = [order]
        self.portfolio_handler._place_orders_onto_queue(order_list)
        ret_order = self.portfolio_handler.events_queue.get()
        self.assertEqual(ret_order.ticker, "MSFT")
        self.assertEqual(ret_order.action, "BOT")
        self.assertEqual(ret_order.quantity, 100)

    def test_convert_fill_to_portfolio_update_basic_check(self):
        """
        Verifica il metodo "_convert_fill_to_portfolio_update"
        come controllo di integrità di base.
        """
        fill_event_buy = FillEvent(
            datetime.datetime.utcnow(), "MSFT", "BOT",
            100, "ARCA", Decimal("50.25"), Decimal("1.00")
        )
        self.portfolio_handler._convert_fill_to_portfolio_update(fill_event_buy)
        # Controlla i valori di Portfolio all'interno di PortfolioHandler
        port = self.portfolio_handler.portfolio
        self.assertEqual(port.cur_cash, Decimal("494974.00"))

        # TODO: Completare e verificare che funzioni tramite Interactive Brokers
        fill_event_sell = FillEvent(
            datetime.datetime.utcnow(), "MSFT", "SLD",
            100, "ARCA", Decimal("50.25"), Decimal("1.00")
        )
        self.portfolio_handler._convert_fill_to_portfolio_update(fill_event_sell)

    def test_on_signal_basic_check(self):
        """
        Verifica il metodo "on_signal" come controllo di integrità di base.
        """
        signal_event = SignalEvent("MSFT", "BOT")
        self.portfolio_handler.on_signal(signal_event)
        ret_order = self.portfolio_handler.events_queue.get()
        self.assertEqual(ret_order.ticker, "MSFT")
        self.assertEqual(ret_order.action, "BOT")
        self.assertEqual(ret_order.quantity, 100)


if __name__ == "__main__":
    unittest.main()
