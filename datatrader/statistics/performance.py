from itertools import groupby

import numpy as np
import pandas as pd
from scipy.stats import linregress


def aggregate_returns(returns, convert_to):
    """
    Aggrega i rendimenti per giorno, settimana, mese o anno.
    """
    def cumulate_returns(x):
        return np.exp(np.log(1 + x).cumsum())[-1] - 1

    if convert_to == 'weekly':
        return returns.groupby(
            [lambda x: x.year,
             lambda x: x.month,
             lambda x: x.isocalendar()[1]]).apply(cumulate_returns)
    elif convert_to == 'monthly':
        return returns.groupby(
            [lambda x: x.year, lambda x: x.month]).apply(cumulate_returns)
    elif convert_to == 'yearly':
        return returns.groupby(
            [lambda x: x.year]).apply(cumulate_returns)
    else:
        ValueError('convert_to must be weekly, monthly or yearly')


def create_cagr(equity, periods=252):
    """
    Calcola il tasso di crescita annuale composto (CAGR)
    per il portafoglio, determinando il numero di anni e
    quindi creando un tasso annualizzato composto basato
    sul rendimento totale.

    Parametri:
    equity - Una serie di pandas che rappresenta la curva equity.
    periods: giornaliero (252), orario (252 * 6.5), minuto (252 * 6.5 * 60) ecc.

    """
    years = len(equity) / float(periods)
    return (equity[-1] ** (1.0 / years)) - 1.0


def create_sharpe_ratio(returns, periods=252):
    """
    Crea lo Sharpe ratio per la strategia, basato su un benchmark pari
    a zero (ovvero nessuna informazione sui tassi privi di rischio).

    Parametri:
    returns - Una serie Pandas che rappresenta i rendimenti percentuali del periodo.
    periods: giornaliero (252), orario (252 * 6.5), minuto (252 * 6.5 * 60) ecc.
    """
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns)


def create_sortino_ratio(returns, periods=252):
    """
    Creare il rapporto Sortino per la strategia, basato su un benchmark pari
    a zero (ovvero nessuna informazione sui tassi privi di rischio).

    Parametri:
    returns - Una serie Pandas che rappresenta i rendimenti percentuali del periodo.
    periods: giornaliero (252), orario (252 * 6.5), minuto (252 * 6.5 * 60) ecc.
    """
    return np.sqrt(periods) * (np.mean(returns)) / np.std(returns[returns < 0])


def create_drawdowns(returns):
    """
    Calcola il massimo drawdown da picco a minimo della curva equity e la
    durata del drawdown. Richiede che pnl_returns sia una serie pandas.

    Parametri:
    equity - Una serie Pandas che rappresenta i rendimenti percentuali del periodo.

    Restituisce:
    drawdown, drawdown_max, duration
    """

    # Calcola la curva dei rendimenti cumulativi
    # e imposta l'High Water Mark
    idx = returns.index
    hwm = np.zeros(len(idx))

    # Crea il high water mark
    for t in range(1, len(idx)):
        hwm[t] = max(hwm[t - 1], returns.iloc[t])

    # Calcola le statistiche di drawdown e durata
    perf = pd.DataFrame(index=idx)
    perf["Drawdown"] = (hwm - returns) / hwm
    perf["Drawdown"].iloc[0] = 0.0
    perf["DurationCheck"] = np.where(perf["Drawdown"] == 0, 0, 1)
    duration = max(
        sum(1 for i in g if i == 1)
        for k, g in groupby(perf["DurationCheck"])
    )
    return perf["Drawdown"], np.max(perf["Drawdown"]), duration


def rsquared(x, y):
    """
    Restituisce il R^2 dove x e y sono array-like.
    """
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    return r_value**2
