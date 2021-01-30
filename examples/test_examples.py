"""
Test examples

One example can be test individually using:

$ nosetests -s -v examples/test_examples.py:TestExamples.test_strategy_backtest

"""
import os
import unittest

from datatrader import settings
import examples.buy_and_hold_backtest
import examples.moving_average_cross_backtest
import examples.monthly_liquidate_rebalance_backtest


class TestExamples(unittest.TestCase):
    """
    Verifica se gli esempi sono eseguiti correttamente
    """
    def setUp(self):
        """
        Imposta la configurazione.
        """
        self.config = settings.TEST
        self.testing = True

    def test_buy_and_hold_backtest(self):
        """
        Verifica buy_and_hold
        Inizia a 2000-01-01 00:00:00
        Finisce a 2014-01-01 00:00:00
        """
        tickers = ["SPY"]
        filename = os.path.join(
            settings.TEST.OUTPUT_DIR,
            "buy_and_hold_backtest.pkl"
        )
        results = examples.buy_and_hold_backtest.run(
            self.config, self.testing, tickers, filename
        )
        for (key, expected) in [
            ('sharpe', 0.25234757),
            ('max_drawdown_pct', 0.79589309),
        ]:
            value = float(results[key])
            self.assertAlmostEqual(expected, value)

    def test_moving_average_cross_backtest(self):
        """
        verifica moving average crossover backtest
        Inizia a 2000-01-01 00:00:00
        Finisce a 2014-01-01 00:00:00
        """
        tickers = ["AAPL", "SPY"]
        filename = os.path.join(
            settings.TEST.OUTPUT_DIR,
            "mac_backtest.pkl"
        )
        results = examples.moving_average_cross_backtest.run(
            self.config, self.testing, tickers, filename
        )
        self.assertAlmostEqual(
            float(results['sharpe']), 0.643009566
        )

    def test_monthly_liquidate_rebalance_backtest(self):
        """
        Verifica della strategia monthly liquidation & rebalance.
        """
        tickers = ["SPY", "AGG"]
        filename = os.path.join(
            settings.TEST.OUTPUT_DIR,
            "monthly_liquidate_rebalance_backtest.pkl"
        )
        results = examples.monthly_liquidate_rebalance_backtest.run(
            self.config, self.testing, tickers, filename
        )
        self.assertAlmostEqual(
            float(results['sharpe']), 0.2710491397280638
        )


if __name__ == "__main__":
    unittest.main()
