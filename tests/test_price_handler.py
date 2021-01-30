import unittest

from datatrader.price_parser import PriceParser
from datatrader.price_handler.historic_csv_tick import HistoricCSVTickPriceHandler
from datatrader.compat import queue
from datatrader import settings


class TestPriceHandlerSimpleCase(unittest.TestCase):
    """
    Verifica dell'inizializzazione di un oggetto PriceHandler
    con un piccolo elenco di ticker. Concatena i dati del
    ticker (pre-generati e memorizzati come un dispositivo)
    e trasmette i tick successivi, controllando che vengano
    restituiti i valori bid-ask corretti.
    """
    def setUp(self):
        """
        Imposta l'oggetto PriceHandler con un piccolo set di ticker iniziali.
        """
        self.config = settings.TEST
        fixtures_path = self.config.CSV_DATA_DIR
        events_queue = queue.Queue()
        init_tickers = ["GOOG", "AMZN", "MSFT"]
        self.price_handler = HistoricCSVTickPriceHandler(
            fixtures_path, events_queue, init_tickers
        )

    def test_stream_all_ticks(self):
        """
        L'inizializzazione della classe aprirà i tre file CSV
        di prova, quindi li unirà e li ordinerà. Verranno quindi
        archiviati in un oggetto "tick_stream".
        Questo verrà utilizzato per lo streaming dei tick.

        """
        # Streaming del tick #1 (GOOG)
        self.price_handler.stream_next()
        self.assertEqual(
            self.price_handler.tickers["GOOG"]["timestamp"].strftime(
                "%d-%m-%Y %H:%M:%S.%f"
            ),
            "01-02-2016 00:00:01.358000"
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["GOOG"]["bid"], 5),
            683.56000
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["GOOG"]["ask"], 5),
            683.58000
        )

        # Streaming del tick #2 (AMZN)
        self.price_handler.stream_next()
        self.assertEqual(
            self.price_handler.tickers["AMZN"]["timestamp"].strftime(
                "%d-%m-%Y %H:%M:%S.%f"
            ),
            "01-02-2016 00:00:01.562000"
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["AMZN"]["bid"], 5),
            502.10001
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["AMZN"]["ask"], 5),
            502.11999
        )

        # Streaming del tick #3 (MSFT)
        self.price_handler.stream_next()
        self.assertEqual(
            self.price_handler.tickers["MSFT"]["timestamp"].strftime(
                "%d-%m-%Y %H:%M:%S.%f"
            ),
            "01-02-2016 00:00:01.578000"
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["MSFT"]["bid"], 5),
            50.14999
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["MSFT"]["ask"], 5),
            50.17001
        )

        # Streaming del tick #10 (GOOG)
        for i in range(4, 11):
            self.price_handler.stream_next()
        self.assertEqual(
            self.price_handler.tickers["GOOG"]["timestamp"].strftime(
                "%d-%m-%Y %H:%M:%S.%f"
            ),
            "01-02-2016 00:00:05.215000"
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["GOOG"]["bid"], 5),
            683.56001
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["GOOG"]["ask"], 5),
            683.57999
        )

        # Streaming del tick #20 (GOOG)
        for i in range(11, 21):
            self.price_handler.stream_next()
        self.assertEqual(
            self.price_handler.tickers["MSFT"]["timestamp"].strftime(
                "%d-%m-%Y %H:%M:%S.%f"
            ),
            "01-02-2016 00:00:09.904000"
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["MSFT"]["bid"], 5),
            50.15000
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["MSFT"]["ask"], 5),
            50.17000
        )

        # Streaming del tick #30 (tick finale, AMZN)
        for i in range(21, 31):
            self.price_handler.stream_next()
        self.assertEqual(
            self.price_handler.tickers["AMZN"]["timestamp"].strftime(
                "%d-%m-%Y %H:%M:%S.%f"
            ),
            "01-02-2016 00:00:14.616000"
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["AMZN"]["bid"], 5),
            502.10015
        )
        self.assertEqual(
            PriceParser.display(self.price_handler.tickers["AMZN"]["ask"], 5),
            502.11985
        )

    def test_subscribe_unsubscribe(self):
        """
        Verifica i metodi 'subscribe_ticker' e 'unsubscribe_ticker'
         e verifica che generino eccezioni quando necessarie.
        """

        # Controlla un ticker già iscritto per assicurarti che non sollevi un'eccezione
        try:
            self.price_handler.subscribe_ticker("GOOG")
        except Exception as E:
            self.fail("subscribe_ticker() raised %s unexpectedly" % E)

        # Annulla l'iscrizione a un ticker corrente
        self.assertTrue("GOOG" in self.price_handler.tickers)
        self.assertTrue("GOOG" in self.price_handler.tickers_data)
        self.price_handler.unsubscribe_ticker("GOOG")
        self.assertTrue("GOOG" not in self.price_handler.tickers)
        self.assertTrue("GOOG" not in self.price_handler.tickers_data)

    def test_get_best_bid_ask(self):
        """
       Verifica che il metodo "get_best_bid_ask" produca
       i valori corretti a seconda della validità del ticker.
        """
        bid, ask = self.price_handler.get_best_bid_ask("AMZN")
        self.assertEqual(PriceParser.display(bid, 5), 502.10001)
        self.assertEqual(PriceParser.display(ask, 5), 502.11999)

        bid, ask = self.price_handler.get_best_bid_ask("C")
        # TODO
        # self.assertEqual(PriceParser.display(bid, 5), None)
        # self.assertEqual(PriceParser.display(ask, 5), None)


if __name__ == "__main__":
    unittest.main()
