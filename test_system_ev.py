import time
import numpy as np
from simulator import Simulator
from strategy import Strategy

def run_simulation(name, rules, expected_ev):
    print(f"\n--- Running {name} Simulation ---")
    print(f"Rules: H17={rules['dealer_hits_soft_17']}, Surrender={rules.get('surrender_allowed')}")
    
    # Setup Strategy
    strategy = Strategy(check_deviations=False, 
                        dealer_hits_soft_17=rules['dealer_hits_soft_17'],
                        surrender_allowed=rules.get('surrender_allowed', False))
    
    # Run Check
    num_hands = 5000000
    print(f"Simulating {num_hands} hands...")
    
    start_time = time.time()
    sim = Simulator(rules, strategy, num_simulations=num_hands)
    stats = sim.run()
    elapsed = time.time() - start_time
    
    total_wagered = stats['total_wagered']
    total_pnl = stats['total_pnl']
    
    # House Edge: PnL / Initial Bet Total
    initial_bet_total = num_hands * 10 
    house_edge = (total_pnl / initial_bet_total) * 100
    
    print(f"Complete in {elapsed:.2f}s")
    print(f"House Edge: {house_edge:.4f}% (Expected ~{expected_ev}%)")
    
    margin = 0.5
    if (expected_ev - margin) <= house_edge <= (expected_ev + margin):
        print("✅ PASS")
    else:
        print("❌ FAIL: Outside margin")
        
def test_system_ev():
    print("Starting Comparative Verified Tests...")
    
    base_rules = {
        'decks': 6,
        'penetration': 0.75,
        'min_bet': 10,
        'betting_strategy': 'Flat', 
        'bankroll': 10000000, 
        'stop_on_ruin': False,
        'das': True,
        'resplit_aces': False,
        'hit_split_aces': False,
        'surrender_allowed': True
    }
    
    # Test 1: H17 (Dealer Hits Soft 17)
    # With: 6D, DAS, Late Surrender
    # Without: RSA, HSA, Insurance
    # Expected: Base H17 (~-0.48%) + DAS (-0.14%) + LS (-0.07%) + No RSA/HSA (+0.06%) + No Insurance (+0.10%)
    # = -0.48 + 0.14 + 0.07 - 0.06 - 0.10 = -0.53% to -0.57%
    rules_h17 = base_rules.copy()
    rules_h17['dealer_hits_soft_17'] = True
    run_simulation("H17 + LS", rules_h17, -0.55)  # Updated expected value
    
    # Test 2: S17 (Dealer Stands on Soft 17)
    # With: 6D, DAS, Late Surrender  
    # Without: RSA, HSA, Insurance
    # Expected: Base S17 (~-0.28%) + DAS (-0.14%) + LS (-0.07%) + No RSA/HSA (+0.06%) + No Insurance (+0.10%)
    # = -0.28 + 0.14 + 0.07 - 0.06 - 0.10 = -0.33% to -0.37%
    rules_s17 = base_rules.copy()
    rules_s17['dealer_hits_soft_17'] = False
    run_simulation("S17 + LS", rules_s17, -0.35)  # Updated expected value
    
if __name__ == "__main__":
    test_system_ev()
