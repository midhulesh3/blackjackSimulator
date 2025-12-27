import unittest
from deck import Card
from simulator import Simulator

# We need a dummy Simulator instance or mock if we test strict encapsulation,
# but since calculate_hand_value uses no self state, we can just instantiate one cheaply.

class TestHandLogic(unittest.TestCase):
    def setUp(self):
        # Minimal simulator
        self.sim = Simulator(rules={}, strategy=None, num_simulations=0)

    def test_simple_hard_total(self):
        # 10 + 5 = 15
        cards = [Card('10', 'H'), Card('5', 'D')]
        val = self.sim.calculate_hand_value(cards)
        self.assertEqual(val['total'], 15)
        self.assertFalse(val['soft'])
    
    def test_blackjack(self):
        # A + K = 21
        cards = [Card('A', 'H'), Card('K', 'D')]
        val = self.sim.calculate_hand_value(cards)
        self.assertEqual(val['total'], 21)
        self.assertTrue(val['soft']) # A + 10 is considered soft usually in calculation until you stand?
        # Actually soft means "Contains Ace computed as 11". 11+10=21. Yes soft.

    def test_soft_17(self):
        # A + 6 = 17
        cards = [Card('A', 'H'), Card('6', 'D')]
        val = self.sim.calculate_hand_value(cards)
        self.assertEqual(val['total'], 17)
        self.assertTrue(val['soft'])

    def test_hard_17_with_ace(self):
        # A + 6 + 10 = 17 (11+6+10=27 bust -> 1+6+10=17)
        cards = [Card('A', 'H'), Card('6', 'D'), Card('10', 'S')]
        val = self.sim.calculate_hand_value(cards)
        self.assertEqual(val['total'], 17)
        self.assertFalse(val['soft'])

    def test_multiple_aces(self):
        # A + A = 12 (11+1)
        cards = [Card('A', 'H'), Card('A', 'D')]
        val = self.sim.calculate_hand_value(cards)
        self.assertEqual(val['total'], 12)
        self.assertTrue(val['soft'])
        
    def test_multiple_aces_hard(self):
        # A + A + 10 = 12 (1+1+10)
        cards = [Card('A', 'H'), Card('A', 'D'), Card('10', 'S')]
        val = self.sim.calculate_hand_value(cards)
        self.assertEqual(val['total'], 12)
        self.assertFalse(val['soft'])

    def test_pair_logic(self):
        # 10 + K (both value 10)
        cards = [Card('10', 'H'), Card('K', 'D')]
        val = self.sim.calculate_hand_value(cards)
        # Simulator logic: is_pair checks cards[0].value == cards[1].value
        self.assertTrue(val['is_pair']) 

    def test_non_pair(self):
        cards = [Card('10', 'H'), Card('9', 'D')]
        val = self.sim.calculate_hand_value(cards)
        self.assertFalse(val['is_pair'])

if __name__ == '__main__':
    unittest.main()
