import unittest
from strategy import Strategy
from deck import Card

class TestStrategy(unittest.TestCase):
    def setUp(self):
        # Integration test with actual files
        self.strat = Strategy(check_deviations=False, surrender_allowed=True)
        
    def test_hard_16_vs_7(self):
        # 16 vs 7 -> Hit
        hand = {'total': 16, 'soft': False, 'is_pair': False}
        dealer_up = Card('7', 'S')
        action = self.strat.get_action(hand, dealer_up)
        self.assertEqual(action, 'Hit')
        
    def test_hard_16_vs_6(self):
        # 16 vs 6 -> Stand
        hand = {'total': 16, 'soft': False, 'is_pair': False}
        dealer_up = Card('6', 'S')
        action = self.strat.get_action(hand, dealer_up)
        self.assertEqual(action, 'Stand')

    def test_soft_18_vs_9(self):
        # Soft 18 (A,7) vs 9 -> Hit
        hand = {'total': 18, 'soft': True, 'is_pair': False}
        dealer_up = Card('9', 'S')
        action = self.strat.get_action(hand, dealer_up)
        self.assertEqual(action, 'Hit')

    def test_pair_eights_vs_10(self):
        # 8,8 vs 10 -> Split
        hand = {'total': 16, 'soft': False, 'is_pair': True, 'cards': [Card('8','H'), Card('8','D')]}
        dealer_up = Card('10', 'S')
        action = self.strat.get_action(hand, dealer_up, can_split=True)
        self.assertEqual(action, 'Split')

    def test_deviation_16_vs_10(self):
        # Illustrious 18: 16 vs 10. Index 0.
        strat_dev = Strategy(check_deviations=True, counting_system='Hi-Lo')
        
        hand = {'total': 16, 'soft': False, 'is_pair': False}
        dealer_up = Card('10', 'S')
        
        # TC -1 -> Hit
        action_neg = strat_dev.get_action(hand, dealer_up, true_count=-1)
        self.assertEqual(action_neg, 'Hit')
        
        # TC 0 -> Stand
        action_pos = strat_dev.get_action(hand, dealer_up, true_count=0)
        self.assertEqual(action_pos, 'Stand')

    def test_fab_four_14_vs_10(self):
        # 14 vs 10. Index +3 -> Surrender.
        strat_dev = Strategy(check_deviations=True, counting_system='Hi-Lo', surrender_allowed=True)
        hand = {'total': 14, 'soft': False, 'is_pair': False}
        dealer_up = Card('10', 'S')
        
        # TC +3 -> Surrender
        action = strat_dev.get_action(hand, dealer_up, true_count=3, can_surrender=True)
        self.assertEqual(action, 'Surrender')
        
        # TC +2 -> Hit (Basic Strategy for 14 vs 10 is Hit)
        action_low = strat_dev.get_action(hand, dealer_up, true_count=2, can_surrender=True)
        self.assertEqual(action_low, 'Hit')

if __name__ == '__main__':
    unittest.main()
