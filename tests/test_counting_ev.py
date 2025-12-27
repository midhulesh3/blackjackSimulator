import time
from simulator import Simulator
from strategy import Strategy

def run_counting_test():
    print("\n--- Running Counting EV Test (Hi-Lo, Spread 1-12) ---")
    
    rules = {
        'decks': 6,
        'penetration': 0.75,
        'min_bet': 10,
        'betting_strategy': 'Linear',
        'ramp_start': 1,
        'ramp_end': 5,
        'max_spread': 12, # 12x min bet ($120)
        'bankroll': 10000000,
        'stop_on_ruin': False,
        'dealer_hits_soft_17': False, # S17
        'das': True,
        'resplit_aces': False,
        'hit_split_aces': False,
        'surrender_allowed': True,
        'insurance_allowed': True
    }
    
    strategy = Strategy(
        check_deviations=True, # Enable Deviations
        counting_system='Hi-Lo',
        dealer_hits_soft_17=False,
        surrender_allowed=True
    )
    
    num_hands = 2000000
    print(f"Simulating {num_hands} hands...")
    
    start_time = time.time()
    sim = Simulator(rules, strategy, num_simulations=num_hands)
    stats = sim.run()
    elapsed = time.time() - start_time
    
    total_wagered = stats['total_wagered']
    total_pnl = stats['total_pnl']
    
    if total_wagered == 0:
        print("Error: Total wagered is 0")
        return

    # EV as % of Total Wagered (Advantage)
    player_advantage = (total_pnl / total_wagered) * 100
    
    print(f"Complete in {elapsed:.2f}s")
    print(f"Total Wagered: ${total_wagered:,.0f}")
    print(f"Total PnL: ${total_pnl:,.2f}")
    print(f"Player Advantage (EV): {player_advantage:.4f}%")
    
    # Check bounds
    if player_advantage > 1.0:
        print("✅ PASS: EV > 1.0%")
    elif player_advantage > 0.5:
        print("⚠️ WARN: EV between 0.5% and 1.0%")
    else:
        print("❌ FAIL: EV <= 0.5%")

if __name__ == "__main__":
    run_counting_test()
