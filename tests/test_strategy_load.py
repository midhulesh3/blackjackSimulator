from strategy import Strategy

# Test strategy loading
strategy = Strategy(check_deviations=False, 
                    dealer_hits_soft_17=False,
                    surrender_allowed=True)

print("Hard Strategy (sample):")
print(f"  Hard 16 vs 10: {strategy.hard_strategy.get(16, ['?']*10)[8]}")  # Should be Rh
print(f"  Hard 12 vs 3: {strategy.hard_strategy.get(12, ['?']*10)[1]}")   # Should be H
print(f"  Hard 9 vs 3: {strategy.hard_strategy.get(9, ['?']*10)[1]}")     # Should be Dh

print("\nSoft Strategy (sample):")
print(f"  Soft 18 vs 2: {strategy.soft_strategy.get(18, ['?']*10)[0]}")   # Should be Ds
print(f"  Soft 17 vs 2: {strategy.soft_strategy.get(17, ['?']*10)[0]}")   # Should be H

print("\nPair Strategy (sample):")  
print(f"  8,8 vs 10: {strategy.pair_strategy.get('8', ['?']*10)[8]}")     # Should be P
print(f"  A,A vs 10: {strategy.pair_strategy.get('A', ['?']*10)[8]}")     # Should be P
