from .base import AbstractStatistics
from ..compat import pickle
from ..price_parser import PriceParser

import datetime
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


class SimpleStatistics(AbstractStatistics):
    """
    Simple Statistics fornisce un semplice esempio di statistiche
    che possono essere raccolte tramite il trading.

    Le statistiche incluse sono Sharpe Ratio, Drawdown, Max Drawdown,
    Max Drawdown Duration.

    TODO prevedere Alpha/Beta, comparazione della strategia con il benchmark.
    TODO verificare la speed -- prevede l'esecusione per ogni tick o comunque per trade sotto il minuto
    TODO prevedere slippage, fill rate, ecc..
    TODO costi di commissione?

    TODO prevedere qualche tipo di parametro trading-frequency parameter nel setup.
    Per il calcolo dello Sharpe bisogna conoscere se si riferisce a timeframe
    giornaliero, orario, un minuto, ecc.
    """
    def __init__(self, config, portfolio_handler):
        """
        Prevede un portfolio handler.
        """
        self.config = config
        self.drawdowns = [0]
        self.equity = []
        self.equity_returns = [0.0]
        # Inizializza il timeseries. Il corretto timestamp non è ancora disponibile.
        self.timeseries = ["0000-00-00 00:00:00"]
        # Inizializzazione in modo che il primo step dei calcoli sia corretto.
        current_equity = PriceParser.display(portfolio_handler.portfolio.equity)
        self.hwm = [current_equity]
        self.equity.append(current_equity)

    def update(self, timestamp, portfolio_handler):
        """
        Aggiorna tutte le statistiche che devono essere tracciate nel tempo.
        """
        if timestamp != self.timeseries[-1]:
            # Ricava il valore equity del Portfolio
            current_equity = PriceParser.display(portfolio_handler.portfolio.equity)
            self.equity.append(current_equity)
            self.timeseries.append(timestamp)

            # Calcula il rendimento percentuale tra l'attuale e il precedente valore dell'equity.
            pct = ((self.equity[-1] - self.equity[-2]) / self.equity[-1]) * 100
            self.equity_returns.append(round(pct, 4))
            # Calcola il drawdown.
            self.hwm.append(max(self.hwm[-1], self.equity[-1]))
            self.drawdowns.append(self.hwm[-1] - self.equity[-1])

    def get_results(self):
        """
        Restituisci un dizionario con tutti i risultati e le statistiche importanti.
        """

        # Modifica le serie temporali solo nell'ambito locale. Inizializziamo
        # con 0-date, ma potrebbe mostrare una data di inizio realistica.

        timeseries = self.timeseries
        timeseries[0] = pd.to_datetime(timeseries[1]) - pd.Timedelta(days=1)

        statistics = {}
        statistics["sharpe"] = self.calculate_sharpe()
        statistics["drawdowns"] = pd.Series(self.drawdowns, index=timeseries)
        statistics["max_drawdown"] = max(self.drawdowns)
        statistics["max_drawdown_pct"] = self.calculate_max_drawdown_pct()
        statistics["equity"] = pd.Series(self.equity, index=timeseries)
        statistics["equity_returns"] = pd.Series(self.equity_returns, index=timeseries)

        return statistics

    def calculate_sharpe(self, benchmark_return=0.00):
        """
        Calcola il sharpe ratio della curva equity dei rendimenti.

        Prevede un benchmark_return, ad esempio, 0,01 per 1%
        """
        excess_returns = pd.Series(self.equity_returns) - benchmark_return / 252

        # Restituire il Sharpe ratio annualizzato in base ai rendimenti giornalieri in eccesso
        return round(self.annualised_sharpe(excess_returns), 4)

    def annualised_sharpe(self, returns, N=252):
        """
        Calcola il Sharpe ratio annualizzato di un flusso di rendimenti in base a
        un numero di periodi di trading, N è impostato a 252 per definizione,
        che quindi presuppone un flusso di rendimenti giornalieri.

        La funzione assume che i rendimenti siano gli eccessi/residui
        dei rendimenti rispetto a un benchmark.
        """
        return np.sqrt(N) * returns.mean() / returns.std()

    def calculate_max_drawdown_pct(self):
        """
        Calcola il calo percentuale relativo al "peggior" drawdown visto.
        """
        drawdown_series = pd.Series(self.drawdowns)
        equity_series = pd.Series(self.equity)
        bottom_index = drawdown_series.idxmax()
        try:
            top_index = equity_series[:bottom_index].idxmax()
            pct = (
                (equity_series.iloc[top_index] - equity_series.iloc[bottom_index]) /
                equity_series.iloc[top_index] * 100
            )
            return round(pct, 4)
        except ValueError:
            return np.nan

    def plot_results(self):
        """
        Un semplice script per tracciare il bilancio del portafoglio,
        o "curva di equity", in funzione del tempo.
        """
        sns.set_palette("deep", desat=.6)
        sns.set_context(rc={"figure.figsize": (8, 4)})

        # Visualizza due grafici: la curva Equity curve e i rendimenti di periodo
        fig = plt.figure()
        fig.patch.set_facecolor('white')

        df = pd.DataFrame()
        df["equity"] = pd.Series(self.equity, index=self.timeseries)
        df["equity_returns"] = pd.Series(self.equity_returns, index=self.timeseries)
        df["drawdowns"] = pd.Series(self.drawdowns, index=self.timeseries)

        # Visualizza la curva equity
        ax1 = fig.add_subplot(311, ylabel='Equity Value')
        df["equity"].plot(ax=ax1, color=sns.color_palette()[0])

        # Visualizza i rendimenti
        ax2 = fig.add_subplot(312, ylabel='Equity Returns')
        df['equity_returns'].plot(ax=ax2, color=sns.color_palette()[1])

        # drawdown, max_dd, dd_duration = self.create_drawdowns(df["Equity"])
        ax3 = fig.add_subplot(313, ylabel='Drawdowns')
        df['drawdowns'].plot(ax=ax3, color=sns.color_palette()[2])

        # Rotate le date
        fig.autofmt_xdate()

        # Visualizza la figura
        plt.show()

    def get_filename(self, filename=""):
        if filename == "":
            now = datetime.datetime.utcnow()
            filename = "statistics_" + now.strftime("%Y-%m-%d_%H%M%S") + ".pkl"
            filename = os.path.expanduser(os.path.join(self.config.OUTPUT_DIR, filename))
        return filename

    def save(self, filename=""):
        filename = self.get_filename(filename)
        print("Save results to '%s'" % filename)
        with open(filename, 'wb') as fd:
            pickle.dump(self, fd)
