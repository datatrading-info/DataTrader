from .order.suggested import SuggestedOrder
from .portfolio import Portfolio


class PortfolioHandler(object):
    def __init__(
        self, initial_cash, events_queue,
        price_handler, position_sizer, risk_manager
    ):
        """
        Il PortfolioHandler è progettato per interagire con un
        backtest o trading dal vivo, in generale una architettura
        basato sugli eventi. Espone due metodi, on_signal e
        on_fill, che gestiscono come gli oggetti SignalEvent
        e FillEvent vengono trattati.

        Ogni PortfolioHandler contiene un oggetto Portfolio,
        che memorizza gli effettivi oggetti Posizione.

        Il PortfolioHandler accetta un handle per un oggetto
        PositionSizer che determina un meccanismo, basato sul
        Portfolio corrente, per dimensionare un nuovo Ordine.

        PortfolioHandler prende anche un handle per il
        RiskManager, che viene utilizzato per modificare qualsiasi
        Ordine in modo da rimanere in linea con i parametri di rischio.
        """
        self.initial_cash = initial_cash
        self.events_queue = events_queue
        self.price_handler = price_handler
        self.position_sizer = position_sizer
        self.risk_manager = risk_manager
        self.portfolio = Portfolio(price_handler, initial_cash)

    def _create_order_from_signal(self, signal_event):
        """
        Prende un oggetto SignalEvent e lo usa per creare un oggetto
        SuggestedOrder. Questi non sono oggetti OrderEvent,
        poiché devono ancora essere inviati all'oggetto RiskManager.
        In questa fase sono semplicemente "suggerimenti" che il
        RiskManager verificherà, modificherà o eliminerà.
        """
        if signal_event.suggested_quantity is None:
            quantity = 0
        else:
            quantity = signal_event.suggested_quantity
        order = SuggestedOrder(
            signal_event.ticker,
            signal_event.action,
            quantity=quantity
        )
        return order

    def _place_orders_onto_queue(self, order_list):
        """
        Una volta che il RiskManager ha verificato, modificato o eliminato
        ogni oggetto Ordine, vengono inseriti nella coda degli eventi,
        per essere infine eseguiti dal ExecutionHandler.
        """
        for order_event in order_list:
            self.events_queue.put(order_event)

    def _convert_fill_to_portfolio_update(self, fill_event):
        """
        Al ricevimento di un FillEvent, PortfolioHandler converte
        l'evento in una transazione che viene archiviata nell'oggetto
        Portafoglio. Ciò garantisce che il broker e il portafoglio locale
        siano "sincronizzati".

        Inoltre, a fini di backtest, il valore del portafoglio può
        essere stimato in modo realistico, semplicemente modificando
        il modo in cui l'oggetto ExecutionHandler gestisce lo slippage,
        i costi di transazione, la liquidità e l'impatto sul mercato.
        """
        action = fill_event.action
        ticker = fill_event.ticker
        quantity = fill_event.quantity
        price = fill_event.price
        commission = fill_event.commission
        # Create or modify the position from the fill info
        self.portfolio.transact_position(
            action, ticker, quantity,
            price, commission
        )

    def on_signal(self, signal_event):
        """
        Questo è chiamato dal backtester o dall'architettura del trading live
        per formare gli ordini iniziali dal SignalEvent.

        Questi ordini vengono ridimensionati dall'oggetto PositionSizer e quindi
        inviato al RiskManager per verificarlo, modificarlo o eliminarlo.

        Una volta ricevuti dal RiskManager vengono convertiti in
        oggetti OrderEvent completi e rinviati alla coda degli eventi.
        """
        # Create the initial order list from a signal event
        initial_order = self._create_order_from_signal(signal_event)
        # Size the quantity of the initial order
        sized_order = self.position_sizer.size_order(
            self.portfolio, initial_order
        )
        # Refine or eliminate the order via the risk manager overlay
        order_events = self.risk_manager.refine_orders(
            self.portfolio, sized_order
        )
        # Place orders onto events queue
        self._place_orders_onto_queue(order_events)

    def on_fill(self, fill_event):
        """
        Questo è chiamato dal backtester o dall'architettura del trading live
        per prendere un FillEvent e aggiornare l'oggetto Portfolio con le nuovi
        posizioni o le posizioni modificate.

        In un ambiente di backtest, questi FillEvents verranno simulati
        da un modello che rappresenta l'esecuzione, mentre nel trading dal vivo
        provengono direttamente da un broker (come Interactive Broker).
        """
        self._convert_fill_to_portfolio_update(fill_event)

    def update_portfolio_value(self):
        """
        Aggiorna il portafoglio per riflettere il valore di
        mercato corrente in base all'ultima offerta / domanda
        di ogni ticker.
        """
        self.portfolio._update_portfolio()
