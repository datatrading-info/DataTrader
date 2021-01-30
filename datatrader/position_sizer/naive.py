from .base import AbstractPositionSizer


class NaivePositionSizer(AbstractPositionSizer):
    def __init__(self, default_quantity=100):
        self.default_quantity = default_quantity

    def size_order(self, portfolio, initial_order):
        """
        Questo oggetto NaivePositionSizer segue tutti
        i suggerimenti dall'ordine iniziale senza
        modifiche. Utile per testare strategie
        più semplici che non risiedono in un
        portafoglio più ampio gestito dal rischio.
        """
        return initial_order
