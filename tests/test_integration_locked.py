import unittest
from simulator import Simulator
from strategy import Strategy
from tests.mocks.deck_mock import MockDeck

class TestIntegrationLocked(unittest.TestCase):
    def setUp(self):
        self.rules = {
            'min_bet': 100,
            'blackjack_payout': 1.5,
            'dealer_hits_soft_17': True,
            'surrender_allowed': True,
            'insurance_allowed': True
        }
        self.strategy = Strategy()
        self.sim = Simulator(self.rules, self.strategy)
        self.sim.setup_simulation()

    def test_player_blackjack_win(self):
        # Scenario: Player BJ (A, K), Dealer (10, 9) -> Player Win 1.5x
        # Cards dealt order: P1, P2, D1, D2
        cards = [
            ('A', 'S'), ('K', 'H'), # Player
            ('10', 'D'), ('9', 'C') # Dealer
        ]
        # Wait, Deal order is P1, D1, P2, D2?
        # Standard: P1, D1, P2, D2
        # My Sim Logic (Step 1092):
        # player_hand = [deck.deal(), deck.deal()]
        # dealer_hand = [deck.deal(), deck.deal()]
        # So my sim deals: P1, P2, D1, D2. 
        # This is slightly non-standard (usually P, D, P, D). 
        # But consistent within Sim. Logic is P [c1, c2], D [c1, c2].
        
        self.sim.deck = MockDeck(cards)
        
        stats = self.sim.play_round() 
        # Note: play_round doesn't return stats for that round specifically, but updates sim state.
        
        # Check bankroll
        # Bet 100. Win 150. PnL +150.
        # Initial bankroll 10000 -> 10150.
        self.assertEqual(self.sim.current_bankroll, 10150.0)
        self.assertEqual(self.sim.blackjacks, 1)
        self.assertEqual(self.sim.wins, 1)

    def test_dealer_blackjack_loss(self):
        # Scenario: D BJ (A, K). Player (10, 9).
        # Order: P1, P2, D1, D2
        cards = [
            ('10', 'S'), ('9', 'H'), # Player
            ('A', 'D'), ('K', 'C')   # Dealer
        ]
        self.sim.deck = MockDeck(cards)
        self.sim.play_round()
        
        # PnL -100
        self.assertEqual(self.sim.current_bankroll, 9900.0)
        self.assertEqual(self.sim.losses, 1)

    def test_split_then_double(self):
        # Complex Scenario:
        # P: 8, 8 (Split)
        # D: 6 (Weak)
        # H1: 8 + 3 = 11 -> Double -> 10 -> 21
        # H2: 8 + 10 = 18 -> Stand
        # Dealer: 6 + 10 + 5 = 21
        
        # Deal Order (Sim):
        # P: 8, 8
        # D: 6, 10 (Hole)
        # Split Action.
        # H1 dealt: 3. Total 11. Double Action. H1 dealt: 10. (Total 21). End.
        # H2 dealt: 10. Total 18. Stand Action. End.
        # Dealer Play: 6, 10 (16). Hit. 5. Total 21.
        
        # Outcomes:
        # H1 (21) vs D (21) -> Push. (Double bet returned?) Yes.
        # H2 (18) vs D (21) -> Loss.
        
        # Bet 100.
        # H1 Bet 200 (Doubled). Push. PnL 0.
        # H2 Bet 100. Loss. PnL -100.
        # Total PnL: -100.
        
        cards = [
            ('8', 'S'), ('8', 'H'),   # P initial
            ('6', 'D'), ('10', 'C'),  # D initial
            ('3', 'D'),               # H1 Card 2
            ('10', 'H'),              # H1 Double Card
            ('10', 'D'),              # H2 Card 2
            ('5', 'S')                # Dealer Hit
        ]
        
        self.sim.deck = MockDeck(cards)
        self.sim.play_round()
        
        self.assertEqual(self.sim.current_bankroll, 9900.0)
        self.assertEqual(self.sim.losses, 1) # H2 lost
        self.assertEqual(self.sim.pushes, 1) # H1 pushed

if __name__ == '__main__':
    unittest.main()
