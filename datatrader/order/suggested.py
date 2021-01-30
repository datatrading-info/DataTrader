class SuggestedOrder(object):
    """
    Un oggetto SuggestedOrder viene generato dal PortfolioHandler
    per essere inviato all'oggetto PositionSizer e successivamente
    all'oggetto RiskManager. La creazione di un tipo di oggetto
    separato per gli ordini suggeriti e gli ordini finali
    (oggetti OrderEvent) garantisce che un ordine suggerito
    non venga mai negoziato a meno che non sia stato esaminato
    dai livelli di dimensionamento della posizione
    e di gestione del rischio.

    """
    def __init__(self, ticker, action, quantity=0):
        """
        Inizializza il SuggestedOrder. Il valore predefinito
        della quantità è zero poiché PortfolioHandler crea
        questi oggetti prima del dimensionamento della posizione.

        L'oggetto PositionSizer "riempirà" il valore corretto
        prima di inviare il SuggestedOrder al RiskManager.

        Parametri:
        ticker - Il simbolo del ticker, ad es. "GOOG".
        action - "BOT" (per long) o "SLD" (per short)
            o "EXIT" (per la liquidazione).
        quantity - La quantità di azioni da negoziare.

        """
        self.ticker = ticker
        self.action = action
        self.quantity = quantity
