
from simulator import Simulator
from strategy import Strategy
from card import Card
from deck import Deck

def test_mechanics():
    print("Testing Mechanics...")
    
    # Test 1: Deck
    d = Deck(num_decks=1)
    print(f"Deck initialized with {len(d.cards)} cards. Remaining: {d.decks_remaining:.2f}")
    assert len(d.cards) == 52
    
    # Test 2: Strategy - Basic Lookup
    strat = Strategy()
    # Hard 16 vs 10 -> Hit? No, Basic says Hit 16 vs 7-A (actually Surrender/Hit). 
    # My table says 'H' for 16 vs 10? Wait.
    # Standard BS: 16 vs 10 is HIT (if no surrender).
    # Correct.
    hand = {'total': 16, 'soft': False, 'is_pair': False}
    dealer_card = Card('10', 'H')
    action = strat.get_action(hand, dealer_card)
    print(f"Action for Hard 16 vs 10: {action}")
    assert action == 'Hit'

    # Hard 12 vs 2 -> Hit (only stand 12 vs 4-6)
    action = strat.get_action({'total': 12, 'soft': False, 'is_pair': False}, Card('2', 'D'))
    print(f"Action for Hard 12 vs 2: {action}")
    assert action == 'Hit'
    
    # Splitting 8s
    hand_pair = {'total': 16, 'soft': False, 'is_pair': True, 'cards': [Card('8','D'), Card('8','C')]}
    action = strat.get_basic_action(hand_pair, dealer_card, can_split=True, can_double=True)
    print(f"Action for Pair 8s vs 10: {action}")
    assert action == 'Split'
    
    # Test 3: Simulator Run (Short)
    print("\nRunning Short Simulation...")
    rules = {'decks': 6, 'penetration': 0.75, 'min_bet': 10}
    sim = Simulator(rules, strat, num_simulations=100)
    stats = sim.run()
    
    print(f"Sim finished. Hands: {len(stats['results'])}")
    print(f"Wins: {stats['wins']}, Losses: {stats['losses']}, Pushes: {stats['pushes']}")
    print(f"Total PnL: {stats['total_pnl']}")
    print(f"EV: {stats['ev']:.4f}")
    
    assert len(stats['results']) == 100
    print("\nTest passed!")

if __name__ == '__main__':
    test_mechanics()
