import unittest

from datatrader.price_handler.base import AbstractBarPriceHandler
from datatrader.order.suggested import SuggestedOrder
from datatrader.price_parser import PriceParser
from datatrader.portfolio import Portfolio
from datatrader.position_sizer.rebalance import LiquidateRebalancePositionSizer


class PriceHandlerMock(AbstractBarPriceHandler):
    def __init__(self):
        self.tickers = {
            "AAA": {"adj_close": PriceParser.parse(50.00)},
            "BBB": {"adj_close": PriceParser.parse(100.00)},
            "CCC": {"adj_close": PriceParser.parse(1.00)},
        }

    def get_last_close(self, ticker):
        return self.tickers[ticker]["adj_close"]


class TestLiquidateRebalancePositionSizer(unittest.TestCase):
    def setUp(self):
        price_handler_mock = PriceHandlerMock()
        ticker_weights = {
            "AAA": 0.3,
            "BBB": 0.7
        }
        self.position_sizer = LiquidateRebalancePositionSizer(ticker_weights)
        self.portfolio = Portfolio(price_handler_mock, PriceParser.parse(10000.00))

    def test_will_add_positions(self):
        """
        Verifica che il position sizer aprirà nuove posizioni con i pesi corretti.
        """
        order_a = SuggestedOrder("AAA", "BOT", 0)
        order_b = SuggestedOrder("BBB", "BOT", 0)
        sized_a = self.position_sizer.size_order(self.portfolio, order_a)
        sized_b = self.position_sizer.size_order(self.portfolio, order_b)

        self.assertEqual(sized_a.action, "BOT")
        self.assertEqual(sized_b.action, "BOT")
        self.assertEqual(sized_a.quantity, 60)
        self.assertEqual(sized_b.quantity, 70)

    def test_will_liquidate_positions(self):
        """
        Assicurarsi che le posizioni vengano liquidate completamente quando richiesto.
        Includere un long e uno short.
        """
        self.portfolio._add_position(
            "BOT", "AAA", 100, PriceParser.parse(60.00), 0.0
        )
        self.portfolio._add_position(
            "BOT", "BBB", -100, PriceParser.parse(60.00), 0.0
        )

        exit_a = SuggestedOrder("AAA", "EXIT", 0)
        exit_b = SuggestedOrder("BBB", "EXIT", 0)
        sized_a = self.position_sizer.size_order(self.portfolio, exit_a)
        sized_b = self.position_sizer.size_order(self.portfolio, exit_b)

        self.assertEqual(sized_a.action, "SLD")
        self.assertEqual(sized_b.action, "BOT")
        self.assertEqual(sized_a.quantity, 100)
        self.assertEqual(sized_a.quantity, 100)


if __name__ == "__main__":
    unittest.main()
