import unittest
from simulator import Simulator
from strategy import Strategy
from card import Card
from tests.mocks.deck_mock import MockDeck

class TestFreeBet(unittest.TestCase):
    def test_strategy_overrides(self):
        strat = Strategy(variant='FreeBet')
        
        # Hard 9 vs 10 -> Should Double (Free)
        hand_9 = {'total': 9, 'soft': False, 'is_pair': False, 'cards': [Card('5','H'), Card('4','D')]}
        action = strat.get_action(hand_9, Card('10','C'), can_double=True)
        self.assertEqual(action, 'Double')
        
        # Pair 8s vs 10 -> Should Split (Free)
        hand_8s = {'total': 16, 'soft': False, 'is_pair': True, 'cards': [Card('8','H'), Card('8','D')]}
        action = strat.get_action(hand_8s, Card('10','C'), can_split=True)
        self.assertEqual(action, 'Split')

    def test_free_split_pnl(self):
        # Force a split scenario: P: 8,8 vs D: 6
        # Outcome: Both hands lose.
        # Real Split: -20. Free Split: -10.
        
        cards_input = [
            ('8','S'), ('8','H'), ('6','D'), ('10','C'),
            ('K','S'), ('K','H'), ('5','S')
        ]
        
        rules = {'min_bet': 10, 'max_hands': 4}
        sim = Simulator(rules, Strategy(variant='FreeBet'))
        sim.setup_simulation()
        sim.deck = MockDeck(cards_input)
        
        sim.play_round()
        
        # Check PnL
        pnl = sim.results[0]['pnl']
        self.assertEqual(pnl, -10.0, "Player incorrectly paid for Free Split hand!")

    def test_push_22_logic(self):
        # Scenario: Dealer 22 Pushes (instead of busting)
        # P: 20 vs D: 22.
        # Outcome: Push (PnL 0).
        
        cards = [
            ('K','S'), ('K','H'), ('6','D'), ('10','C'),
            ('6','H') # Dealer hits 16 -> gets 6 -> 22.
        ]
        
        sim = Simulator({}, Strategy(variant='FreeBet'))
        sim.setup_simulation()
        sim.deck = MockDeck(cards)
        sim.play_round()
        
        pnl = sim.results[0]['pnl']
        self.assertEqual(pnl, 0.0, "Dealer 22 did not push!")
        self.assertEqual(sim.pushes, 1)

if __name__ == "__main__":
    unittest.main()
