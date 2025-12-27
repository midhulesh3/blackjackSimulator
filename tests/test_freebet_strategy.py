import unittest
from strategy import Strategy
from card import Card

class TestFreeBetStrategy(unittest.TestCase):
    def test_conservative_soft_play(self):
        # In Standard, Soft 16 vs 5 is Double.
        # In FreeBet, Soft 16 vs 5 is Hit (Paid Double isn't worth it).
        
        # FreeBet Strategy
        strat_free = Strategy(variant='FreeBet')
        hand_s16 = {'total': 16, 'soft': True, 'is_pair': False}
        dealer_5 = Card('5', 'C')
        
        action = strat_free.get_action(hand_s16, dealer_5, can_double=True)
        self.assertEqual(action, 'Hit', "Free Bet should Hit S16 vs 5 (Conservative)")
        
        # Standard Strategy
        strat_std = Strategy(variant='Standard')
        action_std = strat_std.get_action(hand_s16, dealer_5, can_double=True)
        self.assertEqual(action_std, 'Double', "Standard should Double S16 vs 5")
        
    def test_free_actions_still_work(self):
        # 9 vs 10 Double
        strat = Strategy(variant='FreeBet')
        hand_9 = {'total': 9, 'soft': False, 'is_pair': False, 'cards': [Card('5','H'), Card('4','D')]}
        action = strat.get_action(hand_9, Card('10','C'), can_double=True)
        self.assertEqual(action, 'Double')

    def test_push_22_hard_play(self):
        # 12 vs 4: Standard H17 is Stand.
        # Free Bet (Push 22): Hit.
        strat = Strategy(variant='FreeBet')
        hand_12 = {'total': 12, 'soft': False, 'is_pair': False}
        dealer_4 = Card('4', 'C')
        
        action = strat.get_action(hand_12, dealer_4)
        self.assertEqual(action, 'Hit', "Free Bet should Hit 12 vs 4")

if __name__ == '__main__':
    unittest.main()
