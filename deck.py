import random
from card import Card

class Deck:
    def __init__(self, num_decks=6, penetration=0.75):
        self.num_decks = num_decks
        self.penetration = penetration
        self.cards = []
        self.cut_card_index = 0
        self.ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        self.suits = ['♠', '♥', '♦', '♣']
        self.shuffle()

    def shuffle(self):
        self.cards = []
        for _ in range(self.num_decks):
            for suit in self.suits:
                for rank in self.ranks:
                    self.cards.append(Card(rank, suit))
        
        random.shuffle(self.cards)
        
        # Calculate cut card position
        # Penetration of 0.75 means we deal 75% of the cards.
        # So we stop when 25% remain. 
        # But commonly penetration refers to "how deep we go".
        # If penetration is 0.75, we use 75% of the deck.
        num_cards_to_deal = int(len(self.cards) * self.penetration)
        self.cut_card_index = len(self.cards) - num_cards_to_deal
        
        # Burn one card
        # self.cards.pop() 

    def deal(self):
        if not self.cards:
            return None # Should ideally trigger a reshuffle check before this
        return self.cards.pop()

    @property
    def needs_shuffle(self):
        return len(self.cards) <= self.cut_card_index

    @property
    def decks_remaining(self):
        return max(len(self.cards) / 52.0, 0.5) # Minimum 0.5 to avoid division by zero explosions
