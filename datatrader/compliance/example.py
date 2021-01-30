import datetime
import os
import csv
from datatrader.price_parser import PriceParser

from .base import AbstractCompliance


class ExampleCompliance(AbstractCompliance):
    """
    Un modulo Compliance di base che scrive le transazioni
    in un file CSV nella directory di output.
    """

    def __init__(self, config):
        """
        Cancella l'esistente log dei trade per un giorno, lasciando
        solo le intestazioni in un CSV vuoto.

        Consente di eseguire più test retrospettivi in modo semplice,
        ma molto probabilmente lo rende inadatto per un ambiente
        di produzione che richiede una rigorosa registrazione.

        """
        self.config = config
        # Cancella il precedente file CSV
        today = datetime.datetime.utcnow().date()
        self.csv_filename = "tradelog_" + today.strftime("%Y-%m-%d") + ".csv"

        try:
            fname = os.path.expanduser(os.path.join(config.OUTPUT_DIR, self.csv_filename))
            os.remove(fname)
        except (IOError, OSError):
            print("No tradelog files to clean.")

        # Scrive l'header del nuovo file
        fieldnames = [
            "timestamp", "ticker",
            "action", "quantity",
            "exchange", "price",
            "commission"
        ]
        fname = os.path.expanduser(os.path.join(self.config.OUTPUT_DIR, self.csv_filename))
        with open(fname, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    def record_trade(self, fill):
        """
        Aggiungi tutti i dettagli del FillEvent al log CSV dei trade.
        """
        fname = os.path.expanduser(os.path.join(self.config.OUTPUT_DIR, self.csv_filename))
        with open(fname, 'a') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                fill.timestamp, fill.ticker,
                fill.action, fill.quantity,
                fill.exchange, PriceParser.display(fill.price, 4),
                PriceParser.display(fill.commission, 4)
            ])
