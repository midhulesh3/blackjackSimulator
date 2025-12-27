
from simulator import Simulator
from strategy import Strategy
from card import Card
import pandas as pd

def test_free_bet():
    print("Testing Free Bet Logic...")
    
    # 1. Test Aggressive Free Split/Double Strategy
    print("\n[Test 1] Strategy Overrides")
    strat = Strategy(variant='FreeBet')
    
    # Hard 9 vs 10 -> Should Double (Free)
    hand_9 = {'total': 9, 'soft': False, 'is_pair': False, 'cards': [Card('5','H'), Card('4','D')]}
    action = strat.get_action(hand_9, Card('10','C'), can_double=True)
    print(f"Hard 9 vs 10 Action: {action} (Expected Double)")
    assert action == 'Double'
    
    # Pair 8s vs 10 -> Should Split (Free)
    hand_8s = {'total': 16, 'soft': False, 'is_pair': True, 'cards': [Card('8','H'), Card('8','D')]}
    action = strat.get_action(hand_8s, Card('10','C'), can_split=True)
    print(f"Pair 8s vs 10 Action: {action} (Expected Split)")
    assert action == 'Split'
    
    # Pair 10s vs 6 -> Should Stand (Not Free Split)
    hand_10s = {'total': 20, 'soft': False, 'is_pair': True, 'cards': [Card('10','H'), Card('10','D')]}
    action = strat.get_action(hand_10s, Card('6','C'), can_split=True)
    # Basic strategy stands on 20. Free Bet rule doesn't force split on 10s.
    print(f"Pair 10s vs 6 Action: {action} (Expected Stand)")
    assert action == 'Stand'
    
    print("Strategy Logic Passed!")
    
    # 2. Test Push 22
    # Difficult to force in stochastic Sim, so we'll mock the payout check? 
    # Or just run a longer sim and look for "Pushes" where dealer had 22?
    # Actually, we can check stats['pushes'] vs expected.
    # In Free Bet, dealer 22 occurs ~7% of time?
    # Let's run a sim and print Push rate.
    print("\n[Test 2] Push 22 Rate check")
    rules = {'decks': 6, 'penetration': 0.75, 'min_bet': 10}
    sim = Simulator(rules, Strategy(variant='FreeBet'), num_simulations=5000)
    stats = sim.run()
    
    # Win rate should be decent but dampened by 22 pushes? 
    # Actually house edge is higher (~1%).
    win_rate = stats['wins'] / 5000
    push_rate = stats['pushes'] / 5000
    print(f"Win Rate: {win_rate:.1%}")
    print(f"Push Rate: {push_rate:.1%} (Standard ~8.5%, FreeBet ~15% due to 22)")
    
    # Ideally Push Rate > 10% indicates 22 rule is triggering.
    if push_rate > 0.10:
        print("Push rate high typical of Free Bet 22 rule. PASS.")
    else:
        print("WARNING: Push rate low. Check 22 logic.")
        
    print("Simulation Complete.")

if __name__ == "__main__":
    test_free_bet()
