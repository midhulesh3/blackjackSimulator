
from simulator import Simulator
from strategy import Strategy
import pandas as pd

def test_betting():
    print("Testing Betting Strategies...")
    
    # --- Test 1: Linear Spread ---
    print("\n[Test 1] Linear Spread")
    rules = {
        'decks': 6, 'penetration': 0.75, 'min_bet': 10,
        'betting_strategy': 'Linear',
        'ramp_start': 1, 'ramp_end': 5, 'max_spread': 10
    }
    # We need a strategy to run sim, but it doesn't matter for betting test
    sim = Simulator(rules, Strategy(), num_simulations=5000)
    stats = sim.run()
    
    df = pd.DataFrame(stats['results'])
    
    # Check TC < 1
    low_tc = df[df['true_count'] < 1]
    if len(low_tc) > 0:
        avg_bet = low_tc['bet'].mean()
        print(f"Avg Bet for TC < 1 (Expected 10): {avg_bet:.2f}")
        
        # Debug: Print anomalies
        anomalies = low_tc[low_tc['bet'] > 10]
        if len(anomalies) > 0:
            print("Found anomalies (TC < 1 but Bet > 10):")
            print(anomalies[['true_count', 'bet']].head())
            
        assert abs(avg_bet - 10) < 0.1
        
    # Check TC > 5
    high_tc = df[df['true_count'] > 5]
    if len(high_tc) > 0:
        avg_bet = high_tc['bet'].mean()
        print(f"Avg Bet for TC > 5 (Expected 100): {avg_bet:.2f}")
        assert abs(avg_bet - 100) < 0.1
        
    # Check TC ~ 3 (Midpoint)
    mid_tc = df[(df['true_count'] >= 2.9) & (df['true_count'] <= 3.1)]
    if len(mid_tc) > 0:
        avg_bet = mid_tc['bet'].mean()
        # Scale 1->5. Range 4. TC 3 is +2 from start 1. So 2/4 = 50% spread.
        # 10 to 100. Delta 90. 50% is 45. 10+45 = 55.
        print(f"Avg Bet for TC ~3 (Expected ~55): {avg_bet:.2f}")
        # Allow integer rounding variance
        assert 50 <= avg_bet <= 60
    
    print("Linear Spread Passed!")

    # --- Test 2: Custom Map ---
    print("\n[Test 2] Custom Map")
    rules = {
        'decks': 6, 'penetration': 0.75, 'min_bet': 10,
        'betting_strategy': 'Custom',
        'custom_bet_map': {'1': 2, '3': 5} # TC 1->2x, TC 3->5x
    }
    sim = Simulator(rules, Strategy(), num_simulations=5000)
    stats = sim.run()
    df = pd.DataFrame(stats['results'])
    
    # TC < 1 -> 1x (10)
    low = df[df['true_count'] < 1]
    if len(low) > 0:
        assert abs(low['bet'].mean() - 10) < 0.1
        
    # 1 <= TC < 3 -> 2x (20)
    mid = df[(df['true_count'] >= 1) & (df['true_count'] < 3)]
    if len(mid) > 0:
        print(f"Avg Bet for 1 <= TC < 3 (Expected 20): {mid['bet'].mean():.2f}")
        assert abs(mid['bet'].mean() - 20) < 0.1
        
    # TC >= 3 -> 5x (50)
    high = df[df['true_count'] >= 3]
    if len(high) > 0:
        print(f"Avg Bet for TC >= 3 (Expected 50): {high['bet'].mean():.2f}")
        assert abs(high['bet'].mean() - 50) < 0.1
        
    print("Custom Map Passed!")

if __name__ == "__main__":
    test_betting()
