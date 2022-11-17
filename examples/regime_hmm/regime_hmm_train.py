# regime_hmm_train.py

import datetime
import pickle
import warnings

from hmmlearn.hmm import GaussianHMM
from matplotlib import cm, pyplot as plt
from matplotlib.dates import YearLocator, MonthLocator
import numpy as np
import pandas as pd
import seaborn as sns


def obtain_prices_df(csv_filepath, end_date):
    """
    Legge i prezzi dal file CSV e li carica in un Dataframe,
    filtra per data di fine e calcola i rendimenti percentuali.
    """
    df = pd.read_csv(
        csv_filepath, header=0,
        names=[
            "Date", "Open", "High", "Low",
            "Close", "Volume", "Adj Close"
        ],
        index_col="Date", parse_dates=True
    )
    df["Returns"] = df["Adj Close"].pct_change()
    df = df[:end_date.strftime("%Y-%m-%d")]
    df.dropna(inplace=True)
    return df

def plot_in_sample_hidden_states(hmm_model, df):
    """
    Traccia il grafico dei prezzi di chiusura rettificati
    mascherati dagli stati nascosti nel campione come
    meccanismo per comprendere i regimi di mercato.
    """
    # Array con gli stati nascosti previsti
    hidden_states = hmm_model.predict(df["Returns"])
    # Crea il grafico formattato correttamente
    fig, axs = plt.subplots(
        hmm_model.n_components,
        sharex=True, sharey=True
    )
    colours = cm.rainbow(
        np.linspace(0, 1, hmm_model.n_components)
    )
    for i, (ax, colour) in enumerate(zip(axs, colours)):
        mask = hidden_states == i
        ax.plot_date(
            df.index[mask],
            df["Adj Close"][mask],
            ".", linestyle='none',
            c=colour
        )
        ax.set_title("Hidden State #%s" % i)
        ax.xaxis.set_major_locator(YearLocator())
        ax.xaxis.set_minor_locator(MonthLocator())
        ax.grid(True)
    plt.show()


if __name__ == "__main__":
    # Nasconde gli avvisi di deprecazione per sklearn
    warnings.filterwarnings("ignore")

    # Crea il dataframe SPY dal file CSV di Yahoo Finance e
    # formatta correttamente i rendimente per l'uso nell'HMM
    csv_filepath = "/path/to/your/data/SPY.csv"
    pickle_path = "/path/to/your/model/hmm_model_spy.pkl"
    end_date = datetime.datetime(2004, 12, 31)
    spy = obtain_prices_df(csv_filepath, end_date)
    rets = np.column_stack([spy["Returns"]])

    # Crea il Gaussian Hidden markov Model e lo adatta ai
    # dati dei rendimenti di SPY, visualizzando il punteggio
    hmm_model = GaussianHMM(
        n_components=2, covariance_type="full", n_iter=1000
    ).fit(rets)
    print("Model Score:", hmm_model.score(rets))

    # Grafico dei valori di chiusura degli stati nascosti del campione
    plot_in_sample_hidden_states(hmm_model, spy)

    print("Pickling HMM model...")
    pickle.dump(hmm_model, open(pickle_path, "wb"))
    print("...HMM model pickled.")