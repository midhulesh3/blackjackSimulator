from simulator import Simulator
from strategy import Strategy

# Simple test - run just 1000 hands and check the basics
def test_basic():
    rules = {
        'decks': 6,
        'penetration': 0.75,
        'min_bet': 10,
        'betting_strategy': 'Flat',
        'bankroll': 100000,
        'stop_on_ruin': False,
        'dealer_hits_soft_17': False,  # S17
        'das': True,
        'resplit_aces': False,
        'hit_split_aces': False,
        'surrender_allowed': True
    }
    
    strategy = Strategy(check_deviations=False, 
                        dealer_hits_soft_17=False,
                        surrender_allowed=True)
    
    sim = Simulator(rules, strategy, num_simulations=1000)
    stats = sim.run()
    
    print("\n=== Results for 1000 Hands ===")
    print(f"Wins: {stats['wins']}")
    print(f"Losses: {stats['losses']}")
    print(f"Pushes: {stats['pushes']}")
    print(f"Total PnL: ${stats['total_pnl']:.2f}")
    print(f"Total Wagered: ${stats['total_wagered']:.2f}")
    print(f"Avg Bet per Hand: ${stats['total_wagered']/1000:.2f}")
    
    # House Edge
    initial_bets = 1000 * 10  # num_hands * min_bet
    house_edge = (stats['total_pnl'] / initial_bets) * 100
    print(f"House Edge (PnL/Initial Bet): {house_edge:.4f}%")
    
    # Check win rate
    total_decisions = stats['wins'] + stats['losses'] + stats['pushes']
    win_rate = stats['wins'] / total_decisions * 100 if total_decisions > 0 else 0
    loss_rate = stats['losses'] / total_decisions * 100 if total_decisions > 0 else 0
    push_rate = stats['pushes'] / total_decisions * 100 if total_decisions > 0 else 0
    
    print(f"\nWin Rate: {win_rate:.2f}%")
    print(f"Loss Rate: {loss_rate:.2f}%")
    print(f"Push Rate: {push_rate:.2f}%")
    print(f"Total Decisions: {total_decisions}")
    
    # Expected values for S17 with Late Surrender:
    # Win rate ~43%, Loss rate ~49%, Push rate ~8%
    # House edge ~-0.45%
    
if __name__ == "__main__":
    test_basic()
