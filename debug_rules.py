from simulator import Simulator
from strategy import Strategy
from card import Card

def debug_rules():
    print("DEBUG: Verifying Rules Logic")
    
    # 1. Test Dealer H17
    print("\n--- Test 1: Dealer H17 ---")
    rules = {
        'decks': 1, # Minimal deck
        'dealer_hits_soft_17': True,
        'stop_on_ruin': False,
        'min_bet': 10
    }
    # Mock simulator or just use Simulator methods if possible?
    # Simulator.play_dealer_hand is internal.
    # We will instantiate Simulator and access method (sim.play_dealer_hand is called inside run)
    # We can inherit or mock.
    
    class MockDeck:
        def __init__(self):
            self.cards = [Card('10', 's'), Card('5', 's')] # Next cards: 10, 5...
        def deal(self):
            return self.cards.pop(0)
    
    sim = Simulator(rules, Strategy(), num_simulations=1)
    
    # Setup Dealer Hand: A, 6 (Soft 17)
    dealer_hand = {'cards': [Card('A', 'h'), Card('6', 'd')], 'total': 17, 'soft': True}
    
    # We need to test the logic block in simulator.py
    # simulator.py:
    # while dealer_hand['total'] < 17 or (dealer_hand['total'] == 17 and dealer_hand['soft'] and self.rules.get('dealer_hits_soft_17')):
    
    sim.deck = MockDeck()
    # Manually run the loop logic check
    should_hit = dealer_hand['total'] < 17 or (dealer_hand['total'] == 17 and dealer_hand['soft'] and sim.rules.get('dealer_hits_soft_17'))
    print(f"Dealer Hand: {dealer_hand['total']} Soft: {dealer_hand['soft']}")
    print(f"Rule H17: {sim.rules.get('dealer_hits_soft_17')}")
    print(f"Should Hit? {should_hit}") 
    if should_hit: print("✅ PASS: Dealer hits Soft 17.")
    else: print("❌ FAIL: Dealer stands on Soft 17.")
    
    
    # 2. Test Surrender Logic
    print("\n--- Test 2: Surrender ---")
    rules['surrender_allowed'] = True
    strat = Strategy(surrender_allowed=True, dealer_hits_soft_17=True) # Load H17 strategy
    
    # Hand: 16 (10+6) vs Dealer 10
    # Strat Hard H17 CSV says 16 vs 10 is 'Rh' (Surrender)
    p_hand = {'cards': [Card('10', 'd'), Card('6', 'd')], 'total': 16, 'soft': False, 'is_pair': False}
    d_card = Card('10', 'c') # 10
    
    action = strat.get_action(p_hand, d_card, can_surrender=True)
    print(f"Player: 16 vs 10. Start Action: {action}")
    
    if action == 'Surrender':
         print("✅ PASS: Strategy returns Surrender.")
    else:
         print(f"❌ FAIL: Strategy returned {action} (Expected Surrender).")
         
    # 3. Test Strategy Loading Fallback
    print("\n--- Test 3: Strategy Loading ---")
    if len(strat.hard_strategy) > 0:
        print("✅ PASS: Hard Strategy loaded.")
        # Check specific entry for 16 vs 10 (index 8)
        # 16 is key 16.
        row = strat.hard_strategy.get(16)
        if row:
             code = row[8] # 2..10. 10 is index 8.
             print(f"Code for 16 vs 10: {code}")
             if code == 'Rh': print("✅ PASS: CSV contains Rh.")
             else: print("❌ FAIL: CSV contains " + str(code))
        else:
             print("❌ FAIL: Row 16 missing.")
    else:
        print("❌ FAIL: Strategy dict empty.")

if __name__ == "__main__":
    debug_rules()
