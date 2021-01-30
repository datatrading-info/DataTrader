from math import floor

from .base import AbstractPositionSizer
from datatrader.price_parser import PriceParser


class LiquidateRebalancePositionSizer(AbstractPositionSizer):
    """
    Effettua una periodica liquidazione completa e ribilanciamento
    del Portafoglio.
    Ciò si ottiene determinando se l'ordine è di tipo "EXIT" o
    "BOT / SLD".

    Nel primo caso, viene determinata la quantità corrente di
    azioni nel ticker e quindi BOT o SLD per portare a zero
    la posizione.
    In quest'ultimo caso, l'attuale quantità di azioni da
    ottenere è determinata da pesi prespecificati e rettificata
    per riflettere il patrimonio netto di conto corrente.
    """
    def __init__(self, ticker_weights):
        self.ticker_weights = ticker_weights

    def size_order(self, portfolio, initial_order):
        """
        Dimensionare l'ordine in modo da riflettere la percentuale
        in dollari dell'attuale dimensione del conto azionario
        in base a pesi ticker pre-specificati.
        """
        ticker = initial_order.ticker
        if initial_order.action == "EXIT":
            # Ottenere la quantità corrente e la liquida
            cur_quantity = portfolio.positions[ticker].quantity
            if cur_quantity > 0:
                initial_order.action = "SLD"
                initial_order.quantity = cur_quantity
            else:
                initial_order.action = "BOT"
                initial_order.quantity = cur_quantity
        else:
            weight = self.ticker_weights[ticker]

            # Determina il valore totale del portafoglio, calcola il peso in
            # dollari e infine determina la quantità intera di azioni da acquistare
            price = portfolio.price_handler.tickers[ticker]["adj_close"]
            price = PriceParser.display(price)
            equity = PriceParser.display(portfolio.equity)
            dollar_weight = weight * equity
            weighted_quantity = int(floor(dollar_weight / price))
            initial_order.quantity = weighted_quantity
        return initial_order
