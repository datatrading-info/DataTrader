"""
Test scripts
"""
import unittest

from datatrader import settings
import datatrader.scripts.generate_simulated_prices


class TestScripts(unittest.TestCase):
    """
    Verifica se gli esempi sono eseguiti correttamente
    """
    def setUp(self):
        """
        Imposta la configurazione.
        """
        self.config = settings.TEST

    def test_generate_simulated_prices(self):
        """
        Verifica il metodo generate_simulated_prices
        """
        datatrader.scripts.generate_simulated_prices.run(
            '',  # outdir
            'GOOG',  # ticker
            700,  # init_price
            42,  # seed
            1.5000,  # s0
            0.02,  # spread
            400,  # mu_dt
            100,  # sigma_dt
            2014,  # year
            1,  # month
            3,  # nb_days (numero di giorni da creare)
            config=self.config
        )
