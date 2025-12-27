import unittest
from simulator import Simulator
from strategy import Strategy
from tests.mocks.deck_mock import MockDeck

class TestSystemLocked(unittest.TestCase):
    def test_deterministic_session(self):
        # Scenario: 5 Hands.
        # Rules: S17, No Surrender.
        # Deal Order: P1, P2, D1, D2. 
        
        # Hand 1: P(20) vs D(17). P stands. D stands. Win.
        # P: K, K. D: 10, 7.
        cards_h1 = [('K','S'), ('K','H'), ('10','D'), ('7','C')]
        
        # Hand 2: P(BJ) vs D(18). Win 1.5.
        # P: A, K. D: 10, 8.
        cards_h2 = [('A','S'), ('K','H'), ('10','D'), ('8','C')]
        
        # Hand 3: P(15) vs D(10). 
        # P: 10, 5. D: 10, 9. 
        # P Hits (15 vs 10). Gets K (25). Bust. Loss.
        # Note: D hole card is D2. D does not play if P busts.
        cards_h3 = [('10','S'), ('5','H'), ('10','D'), ('9','C'), ('K','D')]
        
        # Hand 4: P(8,8) vs D(10). Split.
        # P: 8, 8. D: 10, 10.
        # Split. H1: 8 + K (18). vs D(10). Hit/Stand? 18 vs 10 -> Stand.
        # H2: 8 + K (18). vs D(10). Stand.
        # Dealer: 10, 10 (20). Wins vs 18, 18.
        # Loss x 2.
        cards_h4 = [
             ('8','S'), ('8','H'), ('10','D'), ('10','C'),
             # Split Logic: Pop P2.
             # H1 (P1+New), H2 (P2+New).
             # Card for H1: K.
             # Card for H2: K.
             ('K','S'), ('K','H')
        ]
        
        # Hand 5: D(BJ).
        # P: K, K. D: A, K.
        # P loses immediately (or checks BJ). Loss.
        cards_h5 = [('K','S'), ('K','H'), ('A','D'), ('K','C')]
        
        deck_cards = cards_h1 + cards_h2 + cards_h3 + cards_h4 + cards_h5
        
        rules = {
            'min_bet': 100, 
            'blackjack_payout': 1.5,
            'dealer_hits_soft_17': True,
            'surrender_allowed': False,
            'insurance_allowed': False # simplify
        }
        
        sim = Simulator(rules, Strategy(), num_simulations=5)
        sim.setup_simulation()
        sim.deck = MockDeck(deck_cards)
        
        # Run 5 rounds manually to preserve MockDeck
        for _ in range(5):
            sim.play_round()
            sim.hands_played += 1
            
        results = sim.get_stats()
        
        # Verify
        # Wins: H1 (1), H2 (1) = 2.
        # Losses: H3 (1), H4 (2), H5 (1) = 4.
        self.assertEqual(results['wins'], 2)
        # Losses: H3 (1), H4 (2), H5 (1) = 4.
        self.assertEqual(results['wins'], 2)
        self.assertEqual(results['blackjacks'], 1) 
        self.assertEqual(results['losses'], 4)
        
        # PnL: +100 + 150 - 100 - 200 - 100 = -150.
        self.assertEqual(results['total_pnl'], -150.0)

if __name__ == '__main__':
    unittest.main()
