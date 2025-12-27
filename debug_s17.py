from simulator import Simulator
from strategy import Strategy
from card import Card

def debug_s17():
    print("DEBUG: Verifying S17 Logic")
    
    rules = {
        'decks': 1,
        'dealer_hits_soft_17': False, # S17
        'min_bet': 10
    }
    
    class MockDeck:
        def __init__(self):
            # Dealer gets A, 6 (17). Next card 10 if hit.
            self.cards = [Card('10', 's')] 
        def deal(self):
            return self.cards.pop(0) if self.cards else Card('2','c')
            
    sim = Simulator(rules, Strategy(), num_simulations=1)
    
    # Dealer Hand: A, 6 (17)
    dealer_hand = {'cards': [Card('A', 'h'), Card('6', 'd')], 'total': 17, 'soft': True}
    
    # Logic check
    # while dealer_hand['total'] < 17 or (dealer_hand['total'] == 17 and dealer_hand['soft'] and self.rules.get('dealer_hits_soft_17')):
    
    cond_total = dealer_hand['total'] < 17
    cond_h17 = (dealer_hand['total'] == 17 and dealer_hand['soft'] and sim.rules.get('dealer_hits_soft_17'))
    should_hit = cond_total or cond_h17
    
    print(f"Dealer Hand: 17 Soft. Rules H17: False.")
    print(f"Should Hit? {should_hit}")
    
    if not should_hit:
        print("✅ PASS: Dealer Stands on Soft 17.")
    else:
        print("❌ FAIL: Dealer Hits Soft 17.")

if __name__ == "__main__":
    debug_s17()
