from numpy import sign


class Position(object):
    def __init__(
        self, action, ticker, init_quantity,
        init_price, init_commission,
        bid, ask
    ):
        """
        Imposta il "conto" iniziale della posizione che è zero per
        la maggior parte degli item, ad eccezione dell'iniziale
        acquisto / vendita.

        Quindi calcola i valori iniziali e infine aggiorna il
        valore di mercato della transazione.
        """
        self.action = action
        self.ticker = ticker
        self.quantity = init_quantity
        self.init_price = init_price
        self.init_commission = init_commission

        self.realised_pnl = 0
        self.unrealised_pnl = 0

        self.buys = 0
        self.sells = 0
        self.avg_bot = 0
        self.avg_sld = 0
        self.total_bot = 0
        self.total_sld = 0
        self.total_commission = init_commission

        self._calculate_initial_value()
        self.update_market_value(bid, ask)

    def _calculate_initial_value(self):
        """
        A seconda che l'azione fosse un acquisto o una vendita (" BOT "
        o " SLD ") si calcola il costo medio di acquisto, il costo totale
        di acquisto, prezzo medio e costo basi.

        Infine, calcola il totale netto con e senza commissioni.
        """

        if self.action == "BOT":
            self.buys = self.quantity
            self.avg_bot = self.init_price
            self.total_bot = self.buys * self.avg_bot
            self.avg_price = (self.init_price * self.quantity + self.init_commission) // self.quantity
            self.cost_basis = self.quantity * self.avg_price
        else:  # action == "SLD"
            self.sells = self.quantity
            self.avg_sld = self.init_price
            self.total_sld = self.sells * self.avg_sld
            self.avg_price = (self.init_price * self.quantity - self.init_commission) // self.quantity
            self.cost_basis = -self.quantity * self.avg_price
        self.net = self.buys - self.sells
        self.net_total = self.total_sld - self.total_bot
        self.net_incl_comm = self.net_total - self.init_commission

    def update_market_value(self, bid, ask):
        """
        Il valore di mercato è difficile da calcolare davo che abbiamo accesso
        alla parte superiore del portafoglio ordini tramite Interactive
        Brokers, il che significa che il vero prezzo è sconosciuto
        fino all'esecuzione.

        Tuttavia, può essere stimato tramite il prezzo medio come
        differenza tra bid e ask. Una volta calcolato il valore di mercato,
        questo consente il calcolo del profitto realizzato e non realizzato,
        e la perdita per qualsiasi transazione.
        """
        midpoint = (bid + ask) // 2
        self.market_value = self.quantity * midpoint * sign(self.net)
        self.unrealised_pnl = self.market_value - self.cost_basis

    def transact_shares(self, action, quantity, price, commission):
        """
        Calcola le rettifiche alla classe Position che si verificano
        una volta acquistate e vendute nuove azioni.

        Si preoccupa di aggiornare la media e il totale degli
        acquisti/vendite, calcola i costi base e PnL,
        come effettuato tramite Interactive Brokers TWS.
        """
        self.total_commission += commission

        # Adjust total bought and sold
        if action == "BOT":
            self.avg_bot = (
                self.avg_bot * self.buys + price * quantity
            ) // (self.buys + quantity)
            if self.action != "SLD":  # Increasing long position
                self.avg_price = (
                    self.avg_price * self.buys +
                    price * quantity + commission
                ) // (self.buys + quantity)
            elif self.action == "SLD":  # Closed partial positions out
                self.realised_pnl += quantity * (
                    self.avg_price - price
                ) - commission  # Adjust realised PNL
            self.buys += quantity
            self.total_bot = self.buys * self.avg_bot

        # action == "SLD"
        else:
            self.avg_sld = (
                self.avg_sld * self.sells + price * quantity
            ) // (self.sells + quantity)
            if self.action != "BOT":  # Increasing short position
                self.avg_price = (
                    self.avg_price * self.sells +
                    price * quantity - commission
                ) // (self.sells + quantity)
                self.unrealised_pnl -= commission
            elif self.action == "BOT":  # Closed partial positions out
                self.realised_pnl += quantity * (
                    price - self.avg_price
                ) - commission
            self.sells += quantity
            self.total_sld = self.sells * self.avg_sld

        # Adjust net values, including commissions
        self.net = self.buys - self.sells
        self.quantity = self.net
        self.net_total = self.total_sld - self.total_bot
        self.net_incl_comm = self.net_total - self.total_commission

        # Adjust average price and cost basis
        self.cost_basis = self.quantity * self.avg_price
