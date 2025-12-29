import unittest
from simulator import Simulator
from strategy import Strategy
from tests.mocks.deck_mock import MockDeck

class TestRuinDoubles(unittest.TestCase):
    def test_double_down_causes_negative(self):
        # Scenario: Bankroll 100. Bet 100 (All-in).
        # Hand is 11. Strategy says Double.
        # If we Double, we bet another 100. Total risk 200.
        # If we lose, Bankroll -> -100.
        # Expected: Should be prevented from Doubling? Or capped? 
        # Usually, if you can't cover the double, you can't double.
        
        rules = {
            'decks': 6,
            'min_bet': 100,
            'bankroll': 100,
            'stop_on_ruin': True,
            'betting_strategy': 'Flat',
            'dealer_hits_soft_17': False
        }
        
        sim = Simulator(rules, Strategy())
        sim.setup_simulation()
        
        # P: 6, 5 (11). D: 6.
        # Strategy: Double vs 6.
        # P gets 2 (13). D gets 10, 5 (21). P Loses.
        
        deck_cards = [
            ('6','C'), ('5','D'), ('6','H'), ('10','S'), # P(11), D(6,10)
            ('2','C'), # P Hit (Double card) -> 13
            ('5','H')  # D Hit (16+5=21)
        ]
        
        sim.deck = MockDeck(deck_cards)
        sim.run()
        
        print(f"Final Bankroll (Double Risk): {sim.current_bankroll}")
        self.assertGreaterEqual(sim.current_bankroll, 0, "Double Down caused negative bankroll")

    def test_split_causes_negative(self):
        # Scenario: Bankroll 100. Bet 100.
        # P: 8, 8. Strategy: Split.
        # Split requires another 100. Total risk 200.
        # Lose both -> -100.
        
        rules = {
            'min_bet': 100,
            'bankroll': 100,
            'stop_on_ruin': True
        }
        
        sim = Simulator(rules, Strategy())
        sim.setup_simulation()
        
        # P: 8, 8. D: 10. Split.
        # H1: 8 + 10 (18). vs 20. Lose.
        # H2: 8 + 10 (18). vs 20. Lose.
        
        deck_cards = [
            ('8','C'), ('8','D'), ('10','H'), ('10','S'),
            ('10','C'), # H1
            ('10','D')  # H2
        ]
        
        sim.deck = MockDeck(deck_cards)
        sim.run()
        
        print(f"Final Bankroll (Split Risk): {sim.current_bankroll}")
        self.assertGreaterEqual(sim.current_bankroll, 0, "Split caused negative bankroll")

if __name__ == '__main__':
    unittest.main()
