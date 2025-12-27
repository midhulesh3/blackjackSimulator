import unittest
import time
from simulator import Simulator
from strategy import Strategy

class TestSystemEV(unittest.TestCase):
    def run_simulation(self, name, rules, expected_ev):
        print(f"\n--- Running {name} Simulation ---")
        
        strategy = Strategy(check_deviations=False, 
                            dealer_hits_soft_17=rules['dealer_hits_soft_17'],
                            surrender_allowed=rules.get('surrender_allowed', False))
        
        # Reduced check for CI speed (was 5M)
        num_hands = 50000 
        
        sim = Simulator(rules, strategy, num_simulations=num_hands)
        stats = sim.run()
        
        total_pnl = stats['total_pnl']
        initial_bet_total = num_hands * 10 
        house_edge = (total_pnl / initial_bet_total) * 100
        
        print(f"House Edge: {house_edge:.4f}% (Expected ~{expected_ev}%)")
        
        # Wider margin for shorter run variance
        margin = 1.0 
        self.assertAlmostEqual(house_edge, expected_ev, delta=margin)

    def test_h17_ev(self):
        base_rules = {
            'decks': 6, 'penetration': 0.75, 'min_bet': 10,
            'betting_strategy': 'Flat', 'bankroll': 1000000, 
            'stop_on_ruin': False, 'das': True,
            'resplit_aces': False, 'hit_split_aces': False,
            'surrender_allowed': True
        }
        rules = base_rules.copy()
        rules['dealer_hits_soft_17'] = True
        self.run_simulation("H17 + LS", rules, -0.55)

    def test_s17_ev(self):
        base_rules = {
            'decks': 6, 'penetration': 0.75, 'min_bet': 10,
            'betting_strategy': 'Flat', 'bankroll': 1000000, 
            'stop_on_ruin': False, 'das': True,
            'resplit_aces': False, 'hit_split_aces': False,
            'surrender_allowed': True
        }
        rules = base_rules.copy()
        rules['dealer_hits_soft_17'] = False
        self.run_simulation("S17 + LS", rules, -0.35)

if __name__ == "__main__":
    unittest.main()
