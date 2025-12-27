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

    def test_no_paid_actions_on_free_hands(self):
        # Scenario: Free Hand (e.g. from Split 8s). Hand: Soft 13 (A,2). Dealer: 5.
        # Table says: Double (Dh).
        # Free Double Rule: Only Hard 9-11. So this is a PAID Double.
        # Strategy for Free Hand: Should NOT pay. Should Downgrade to Hit.
        
        strat = Strategy(variant='FreeBet')
        # Manually set is_free_hand=True in call
        hand_s13 = {'total': 13, 'soft': True, 'is_pair': False}
        dealer_5 = Card('5', 'C')
        
        # 1. Check Paid Hand behavior (Baseline)
        action_paid = strat.get_action(hand_s13, dealer_5, can_double=True, is_free_hand=False)
        # Soft 13 vs 5 in freebet_soft.csv: 13,H,H,H,H,H,H,H,H,H,H (Row 13).
        # Wait, let me check freebet_soft.csv content I wrote.
        # Row 13: H,H,H,H,H,H,H,H,H,H.
        # Ah, I made the soft table VERY conservative ("Minimal Paid Doubles").
        # So it might already be Hit.
        
        # Let's find a case where I kept the Double.
        # freebet_soft.csv:
        # 17: H,H,H,H,D,H,H,H,H,H. (vs 6).
        # Soft 17 vs 6.
        hand_s17 = {'total': 17, 'soft': True, 'is_pair': False}
        dealer_6 = Card('6', 'C')
        
        action_paid = strat.get_action(hand_s17, dealer_6, can_double=True, is_free_hand=False)
        self.assertEqual(action_paid, 'Double', "Paid Hand should Double Soft 17 vs 6")
        
        # 2. Check Free Hand behavior
        action_free = strat.get_action(hand_s17, dealer_6, can_double=True, is_free_hand=True)
        self.assertEqual(action_free, 'Hit', "Free Hand should NOT Pay to Double Soft 17 vs 6")

if __name__ == '__main__':
    unittest.main()
