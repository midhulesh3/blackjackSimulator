import unittest
from strategy import Strategy
from simulator import Simulator
from card import Card
from tests.mocks.deck_mock import MockDeck

class TestStrategyCustom(unittest.TestCase):
    def test_custom_hard_strategy_override(self):
        # Default: Hard 20 vs 6 is STAND.
        # Custom: Override to HIT.
        
        # 1. Prepare Custom Table
        # Dict format: {Total: [Actions for 2,3,4,5,6,7,8,9,10,A]}
        # We only need to override 20. Strategy class uses .get(), defaults to Stand/Hit?
        # Actually Strategy loads the whole CSV.
        # If I pass a incomplete dict, what happens?
        # The Strategy logic uses `self.hard_strategy.get(t, ['H']*10)`.
        # So it defaults to Hit list if missing.
        # So I only need to provide the row for 20.
        
        custom_row_20 = ['H'] * 10 # All Hits
        custom_tables = {
            'hard': {20: custom_row_20}
        }
        
        # 2. Initialize Strategy
        strat = Strategy(custom_tables=custom_tables)
        
        # 3. Verify Action
        hand_20 = {'total': 20, 'soft': False, 'is_pair': False}
        dealer_6 = Card('6', 'D')
        
        action = strat.get_action(hand_20, dealer_6)
        self.assertEqual(action, 'Hit', "Custom Strategy should force Hit on 20")
        
    def test_custom_pair_strategy_override(self):
        # Default: 10,10 vs 6 is STAND.
        # Custom: Override to SPLIT.
        
        custom_row_10 = ['P'] * 10 # All Split (P)
        custom_tables = {
            'pair': {'10': custom_row_10} # '10' for T, J, Q, K
        }
        
        strat = Strategy(custom_tables=custom_tables)
        
        hand_10s = {'total': 20, 'soft': False, 'is_pair': True, 'cards': [Card('K','H'), Card('K','D')]}
        dealer_6 = Card('6', 'D')
        
        action = strat.get_action(hand_10s, dealer_6, can_split=True)
        self.assertEqual(action, 'Split', "Custom Strategy should force Split on 10s")

    def test_simulator_execution_with_custom(self):
        # Integration Check
        # Rule: Hit on 20.
        # Scenario: P(20). D(6).
        # P Hits -> Gets 2 (22). Bust.
        # If Standard Strategy -> Stand (20). Win.
        
        custom_row_20 = ['H'] * 10 
        custom_tables = {'hard': {20: custom_row_20}}
        
        strat = Strategy(custom_tables=custom_tables)
        rules = {'min_bet': 10, 'dealer_hits_soft_17': False}
        
        sim = Simulator(rules, strat)
        sim.setup_simulation()
        
        cards = [
            ('10','H'), ('10','D'), ('6','C'), ('10','S'), # P(20), D(6,10)
            ('2','H'), # P Hit -> 22 Bust
            ('10','C') # D hole/next? D doesn't play if P busts.
        ]
        sim.deck = MockDeck(cards)
        
        sim.play_round()
        
        self.assertEqual(sim.losses, 1, "Should lose due to custom Hit on 20")

if __name__ == '__main__':
    unittest.main()
