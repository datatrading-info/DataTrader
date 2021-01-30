import unittest

from datatrader.portfolio import Portfolio
from datatrader.price_parser import PriceParser
from datatrader.price_handler.base import AbstractTickPriceHandler


class PriceHandlerMock(AbstractTickPriceHandler):
    def get_best_bid_ask(self, ticker):
        prices = {
            "GOOG": (PriceParser.parse(705.46), PriceParser.parse(705.46)),
            "AMZN": (PriceParser.parse(564.14), PriceParser.parse(565.14)),
        }
        return prices[ticker]


class TestAmazonGooglePortfolio(unittest.TestCase):
    """
    Prova un portafoglio composto da Amazon e
    Google con vari ordini per creare
    "round-trip" per entrambi.

    Questi ordini sono stati eseguiti in un conto demo
    di Interactive Brokers e verificata l'uguaglianza
    per contanti, equità e PnL.
    """

    def setUp(self):
        """
        Imposta l'oggetto Portfolio che memorizzerà una
        raccolta di oggetti Position, prevedendo
        $500.000,00 USD per il saldo iniziale del conte
        """
        ph = PriceHandlerMock()
        cash = PriceParser.parse(500000.00)
        self.portfolio = Portfolio(ph, cash)

    def test_calculate_round_trip(self):
        """
        P Acquisto/vendita più lotti di AMZN e GOOG
        a vari prezzi / commissioni per controllare
        il calcolo e la gestione dei costi.
        """
        # Acquista 300 AMZN su due transazion
        self.portfolio.transact_position(
            "BOT", "AMZN", 100,
            PriceParser.parse(566.56), PriceParser.parse(1.00)
        )
        self.portfolio.transact_position(
            "BOT", "AMZN", 200,
            PriceParser.parse(566.395), PriceParser.parse(1.00)
        )
        # Acquista 200 GOOG su una transazione
        self.portfolio.transact_position(
            "BOT", "GOOG", 200,
            PriceParser.parse(707.50), PriceParser.parse(1.00)
        )
        # Aggiunge 100 azioni sulla posizione di AMZN
        self.portfolio.transact_position(
            "SLD", "AMZN", 100,
            PriceParser.parse(565.83), PriceParser.parse(1.00)
        )
        # Aggiunge 200 azioni alla posizione di GOOG
        self.portfolio.transact_position(
            "BOT", "GOOG", 200,
            PriceParser.parse(705.545), PriceParser.parse(1.00)
        )
        # Vende 200 azioni di AMZN
        self.portfolio.transact_position(
            "SLD", "AMZN", 200,
            PriceParser.parse(565.59), PriceParser.parse(1.00)
        )
        # Transazioni Multiple costruite in una (in IB)
        # Vendi 300 GOOG dal portfolio
        self.portfolio.transact_position(
            "SLD", "GOOG", 100,
            PriceParser.parse(704.92), PriceParser.parse(1.00)
        )
        self.portfolio.transact_position(
            "SLD", "GOOG", 100,
            PriceParser.parse(704.90), PriceParser.parse(0.00)
        )
        self.portfolio.transact_position(
            "SLD", "GOOG", 100,
            PriceParser.parse(704.92), PriceParser.parse(0.50)
        )
        # Infine vendiamo le rimanenti 100 azioni di GOOG
        self.portfolio.transact_position(
            "SLD", "GOOG", 100,
            PriceParser.parse(704.78), PriceParser.parse(1.00)
        )

        # I numeri seguenti sono derivati dall'account demo di
        # Interactive Brokers usando i seguenti trade con i
        # prezzi forniti dal loro feed dati in demo.
        self.assertEqual(len(self.portfolio.positions), 0)
        self.assertEqual(len(self.portfolio.closed_positions), 2)
        self.assertEqual(PriceParser.display(self.portfolio.cur_cash), 499100.50)
        self.assertEqual(PriceParser.display(self.portfolio.equity), 499100.50)
        self.assertEqual(PriceParser.display(self.portfolio.unrealised_pnl), 0.00)
        self.assertEqual(PriceParser.display(self.portfolio.realised_pnl), -899.50)


if __name__ == "__main__":
    unittest.main()
