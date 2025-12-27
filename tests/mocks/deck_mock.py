from deck import Card

class MockDeck:
    """
    A deterministic deck that deals specific cards in order.
    Useful for testing specific scenarios.
    """
    def __init__(self, cards):
        # cards: list of Card objects or list of tuples ('Rank', 'Suit')
        self.cards = []
        for c in cards:
            if isinstance(c, Card):
                self.cards.append(c)
            else:
                self.cards.append(Card(c[0], c[1]))
                
        self.decks_remaining = 1 # Mock value for TC calculation
        self.needs_shuffle = False

    def deal(self):
        if not self.cards:
            raise ValueError("MockDeck ran out of cards!")
        c = self.cards.pop(0)
        # print(f"DEBUG: Dealt {c}") 
        return c

    def shuffle(self):
        # No-op for mock deck usually, or reset?
        pass
