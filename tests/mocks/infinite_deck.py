import random

from card import Card


class InfiniteDeck:
    """Draws every card independently (sampling with replacement) from a seeded RNG.

    Matches the infinite-deck model used by exact_ev.py, so simulator results can be
    compared directly with the exact house edge. Never needs shuffling.
    """
    _RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self._cards = [Card(r, '♠') for r in self._RANKS]
        self.cards = [None]          # non-empty: Simulator.deal_card() never reshuffles
        self.needs_shuffle = False
        self.decks_remaining = 6
        self.num_decks = None

    def deal(self):
        return self.rng.choice(self._cards)

    def shuffle(self):
        pass
