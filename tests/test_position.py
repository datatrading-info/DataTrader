import unittest

from datatrader.position import Position
from datatrader.price_parser import PriceParser


class TestRoundTripXOMPosition(unittest.TestCase):
    """
    Prova un trade round-trip per Exxon-Mobil dove il trade iniziale
    è un acquisto / long di 100 azioni di XOM, al prezzo di
    $ 74,78, con una commissione di $ 1,00.
    """

    def setUp(self):
        """
        Imposta l'oggetto Position che memorizzerà il PnL.
        """
        self.position = Position(
            "BOT", "XOM", 100,
            PriceParser.parse(74.78), PriceParser.parse(1.00),
            PriceParser.parse(74.78), PriceParser.parse(74.80)
        )

    def test_calculate_round_trip(self):
        """
        Dopo il successivo acquisto, si effettuano altri due acquisti / long
        e poi chiudere la posizione con due ulteriori vendite / short.

        I seguenti prezzi sono stati confrontati con quelli calcolati
        tramite Interactive Brokers 'Trader Workstation (TWS).
        """
        self.position.transact_shares(
            "BOT", 100, PriceParser.parse(74.63), PriceParser.parse(1.00)
        )
        self.position.transact_shares(
            "BOT", 250, PriceParser.parse(74.620), PriceParser.parse(1.25)
        )
        self.position.transact_shares(
            "SLD", 200, PriceParser.parse(74.58), PriceParser.parse(1.00)
        )
        self.position.transact_shares(
            "SLD", 250, PriceParser.parse(75.26), PriceParser.parse(1.25)
        )
        self.position.update_market_value(
            PriceParser.parse(77.75), PriceParser.parse(77.77)
        )

        self.assertEqual(self.position.action, "BOT")
        self.assertEqual(self.position.ticker, "XOM")
        self.assertEqual(self.position.quantity, 0)

        self.assertEqual(self.position.buys, 450)
        self.assertEqual(self.position.sells, 450)
        self.assertEqual(self.position.net, 0)
        self.assertEqual(
            PriceParser.display(self.position.avg_bot, 5), 74.65778
        )
        self.assertEqual(
            PriceParser.display(self.position.avg_sld, 5), 74.95778
        )
        self.assertEqual(PriceParser.display(self.position.total_bot), 33596.00)
        self.assertEqual(PriceParser.display(self.position.total_sld), 33731.00)
        self.assertEqual(PriceParser.display(self.position.net_total), 135.00)
        self.assertEqual(PriceParser.display(self.position.total_commission), 5.50)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), 129.50)

        self.assertEqual(
            PriceParser.display(self.position.avg_price, 3), 74.665
        )
        self.assertEqual(PriceParser.display(self.position.cost_basis), 0.00)
        self.assertEqual(PriceParser.display(self.position.market_value), 0.00)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), 0.00)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 129.50)


class TestRoundTripPGPosition(unittest.TestCase):
    """
    Prova uno trade round-trip per Proctor & Gamble dove il trade iniziale
    è una vendita / short di 100 azioni di PG, al prezzo di
    $ 77,69, con una commissione di $ 1,00.
    """
    def setUp(self):
        self.position = Position(
            "SLD", "PG", 100,
            PriceParser.parse(77.69), PriceParser.parse(1.00),
            PriceParser.parse(77.68), PriceParser.parse(77.70)
        )

    def test_calculate_round_trip(self):
        """
        Dopo la successiva vendita, eseguire altre due vendite / cortometraggi
        e poi chiudere la posizione con altri due acquisti / long.

        I seguenti prezzi sono stati confrontati con quelli calcolati
        tramite Interactive Brokers 'Trader Workstation (TWS).
        """
        self.position.transact_shares(
            "SLD", 100, PriceParser.parse(77.68), PriceParser.parse(1.00)
        )
        self.position.transact_shares(
            "SLD", 50, PriceParser.parse(77.70), PriceParser.parse(1.00)
        )
        self.position.transact_shares(
            "BOT", 100, PriceParser.parse(77.77), PriceParser.parse(1.00)
        )
        self.position.transact_shares(
            "BOT", 150, PriceParser.parse(77.73), PriceParser.parse(1.00)
        )
        self.position.update_market_value(
            PriceParser.parse(77.72), PriceParser.parse(77.72)
        )

        self.assertEqual(self.position.action, "SLD")
        self.assertEqual(self.position.ticker, "PG")
        self.assertEqual(self.position.quantity, 0)

        self.assertEqual(self.position.buys, 250)
        self.assertEqual(self.position.sells, 250)
        self.assertEqual(self.position.net, 0)
        self.assertEqual(
            PriceParser.display(self.position.avg_bot, 3), 77.746
        )
        self.assertEqual(
            PriceParser.display(self.position.avg_sld, 3), 77.688
        )
        self.assertEqual(PriceParser.display(self.position.total_bot), 19436.50)
        self.assertEqual(PriceParser.display(self.position.total_sld), 19422.00)
        self.assertEqual(PriceParser.display(self.position.net_total), -14.50)
        self.assertEqual(PriceParser.display(self.position.total_commission), 5.00)
        self.assertEqual(PriceParser.display(self.position.net_incl_comm), -19.50)

        self.assertEqual(
            PriceParser.display(self.position.avg_price, 5), 77.67600
        )
        self.assertEqual(PriceParser.display(self.position.cost_basis), 0.00)
        self.assertEqual(PriceParser.display(self.position.market_value), 0.00)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), 0.00)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), -19.50)


class TestShortPosition(unittest.TestCase):
    """
    Prova di una posizione short per Proctor & Gamble dove il trade iniziale
    è una vendita / short di 100 azioni di PG, al prezzo di
    $ 77,69, con una commissione di $ 1,00.
    """
    def setUp(self):
        self.position = Position(
            "SLD", "PG", 100,
            PriceParser.parse(77.69), PriceParser.parse(1.00),
            PriceParser.parse(77.68), PriceParser.parse(77.70)
        )

    def test_open_short_position(self):
        self.assertEqual(PriceParser.display(self.position.cost_basis), -7768.00)
        self.assertEqual(PriceParser.display(self.position.market_value), -7769.00)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), -1.00)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)

        self.position.update_market_value(
            PriceParser.parse(77.72), PriceParser.parse(77.72)
        )

        self.assertEqual(PriceParser.display(self.position.cost_basis), -7768.00)
        self.assertEqual(PriceParser.display(self.position.market_value), -7772.00)
        self.assertEqual(PriceParser.display(self.position.unrealised_pnl), -4.00)
        self.assertEqual(PriceParser.display(self.position.realised_pnl), 0.00)


class TestProfitLossBuying(unittest.TestCase):
    """
    Verifica che i PNL non realizzati e realizzati
    stiano funzionando dopo l'inizializzazione
    della posizione, dopo ogni transazione e dopo
    ogni aggiornamento del prezzo
    """
    def setUp(self):
        self.position = Position(
            "BOT", "XOM", 100,
            PriceParser.parse(74.78), PriceParser.parse(1.00),
            PriceParser.parse(74.77), PriceParser.parse(74.79)
        )

    def test_realised_unrealised_calcs(self):
        self.assertEqual(
            PriceParser.display(self.position.unrealised_pnl), -1.00
        )
        self.assertEqual(
            PriceParser.display(self.position.realised_pnl), 0.00
        )

        self.position.update_market_value(
            PriceParser.parse(75.77), PriceParser.parse(75.79)
        )
        self.assertEqual(
            PriceParser.display(self.position.unrealised_pnl), 99.00
        )
        self.position.transact_shares(
            "SLD", 100,
            PriceParser.parse(75.78), PriceParser.parse(1.00)
        )
        self.assertEqual(
            PriceParser.display(self.position.unrealised_pnl), 99.00
        )  # still high
        self.assertEqual(
            PriceParser.display(self.position.realised_pnl), 98.00
        )

        self.position.update_market_value(
            PriceParser.parse(75.77), PriceParser.parse(75.79)
        )
        self.assertEqual(
            PriceParser.display(self.position.unrealised_pnl), 0.00
        )


if __name__ == "__main__":
    unittest.main()
