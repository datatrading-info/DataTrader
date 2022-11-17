# regime_hmm_risk_manager.py

import numpy as np

from datatrader.event import OrderEvent
from datatrader.price_parser import PriceParser
from datatrader.risk_manager.base import AbstractRiskManager

class RegimeHMMRiskManager(AbstractRiskManager):
    """
    Utilizza un modello Hidden Markov precedentemente adattato
    come meccanismo di rilevamento del regime. Il gestore del
    rischio ignora gli ordini che si verificano durante
    un regime non desiderato.

    Ciò spiega anche il fatto che un'operazione può essere
    a cavallo di due regimi separati. Se un ordine di chiusura
    viene ricevuto nel regime non desiderato e l'ordine è aperto,
    verrà chiuso, ma non verranno generati nuovi ordini fino
    al raggiungimento del regime desiderato.
    """
    def __init__(self, hmm_model):
        self.hmm_model = hmm_model
        self.invested = False

    def determine_regime(self, price_handler, sized_order):
        """
        Determina il probabile regime effettuando una previsione sui rendimenti
        dei prezzi di chiusura nell'oggetto PriceHandler e quindi prende
        il valore intero finale come "stato del regime nascosto"
        """
        returns = np.column_stack(
            [np.array(price_handler.adj_close_returns)]
        )
        hidden_state = self.hmm_model.predict(returns)[-1]
        return hidden_state

    def refine_orders(self, portfolio, sized_order):
        """
        Utilizza il modello di Markov nascosto con i rendimenti percentuali
        per determinare il regime corrente, 0 per desiderabile o 1 per
        indesiderabile. Ingressi Long seguiti solo in regime 0, operazioni
        di chiusura sono consentite in regime 1.
        """
        # Determinare il regime previsto HMM come un intero
        # uguale a 0 (desiderabile) o 1 (indesiderabile)
        price_handler = portfolio.price_handler
        regime = self.determine_regime(
            price_handler, sized_order
        )
        action = sized_order.action
        # Crea l'evento dell'ordine, indipendentemente dal regime. Sarà
        # restituito solo se le condizioni corrette sono soddisfatte.
        order_event = OrderEvent(
            sized_order.ticker,
            sized_order.action,
            sized_order.quantity
        )

        # Se abbiamo un regime desiderato, permettiamo gli ordini di acquisto e di
        # vendita normalmente per una strategia di trend following di solo lungo
        if regime == 0:
            if action == "BOT":
                self.invested = True
                return [order_event]
            elif action == "SLD":
                if self.invested == True:
                    self.invested = False
                    return [order_event]
                else:
                    return []
        # Se abbiamo un regime non desiderato, non permetiamo ordini di
        # acquisto e permettiamo solo di chiudere posizioni aperte se la
        # strategia è già a mercato (da un precedenete regime desiderato)
        elif regime == 1:
            if action == "BOT":
                self.invested = False
                return []
            elif action == "SLD":
                if self.invested == True:
                    self.invested = False
                    return [order_event]
                else:
                    return []
