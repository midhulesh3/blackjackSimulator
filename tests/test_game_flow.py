import unittest
from unittest.mock import MagicMock
from simulator import Simulator
from deck import Card

class TestGameFlow(unittest.TestCase):
    def setUp(self):
        self.strategy = MagicMock()
        self.rules = {
            'min_bet': 10,
            'surrender_allowed': True,
            'das': True,
            'resplit_aces': False,
            'hit_split_aces': False
        }
        self.sim = Simulator(self.rules, self.strategy, 0)
        self.sim.deck = MagicMock()
        self.sim.deck.decks_remaining = 1
        self.sim.running_count = 0
        
    def test_double_down(self):
        # Setup: P=11 (6+5), D=10. Action=Double.
        hand = {'cards': [Card('6', 'H'), Card('5', 'D')], 'bet': 10}
        dealer_up = Card('10', 'S')
        
        # Strategy returns Double
        self.strategy.get_action.return_value = 'Double'
        # Deck deals one card (face)
        self.sim.deck.deal.return_value = Card('K', 'H')
        
        finished = self.sim.process_player_turn(hand, dealer_up)
        
        self.assertEqual(len(finished), 1)
        res = finished[0]
        self.assertEqual(len(res['cards']), 3)
        self.assertEqual(res['bet'], 20) # Doubled
        self.assertEqual(res['total'], 21)
        
    def test_surrender(self):
        hand = {'cards': [Card('10', 'H'), Card('6', 'D')], 'bet': 10}
        dealer_up = Card('A', 'S')
        
        self.strategy.get_action.return_value = 'Surrender'
        
        finished = self.sim.process_player_turn(hand, dealer_up)
        
        self.assertTrue(finished[0]['surrendered'])
        self.assertEqual(finished[0]['bet'], 10) # Bet not changed here, handled in settlement
        
    def test_split_aces_forced_stand(self):
        # P = A, A. Split.
        # Hand 1 gets Ten -> 21. Forced Stand (No HSA, No RSA).
        # Hand 2 gets Nine -> 20. Forced Stand.
        
        hand = {'cards': [Card('A', 'H'), Card('A', 'D')], 'bet': 10}
        dealer_up = Card('6', 'S')
        
        # Strategy: Split
        self.strategy.get_action.side_effect = ['Split', 'Stand', 'Stand'] # Fallback
        
        # Mock Deal: 
        # 1. 10 (for H1)
        # 2. 9 (for H2)
        self.sim.deck.deal.side_effect = [Card('10', 'C'), Card('9', 'C')]
        
        finished = self.sim.process_player_turn(hand, dealer_up)
        
        self.assertEqual(len(finished), 2)
        # H1: A+10 = 21 (First finished? No, First appended?)
        # Logic: Pop H1. Play. Append H1. Pop H2. Play. Append H2.
        # So finished[0] is H1. finished[1] is H2.
        
        self.assertEqual(finished[0]['total'], 21) 
        self.assertEqual(finished[1]['total'], 20)
        self.assertTrue(finished[0]['from_split_ace'])

if __name__ == '__main__':
    unittest.main()
