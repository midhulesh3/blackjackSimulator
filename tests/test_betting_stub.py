
from simulator import Simulator
from strategy import Strategy
import numpy as np

# Mock Deck to control count? Hard to do with current Deck class.
# Instead, we can inspect the betting choice method if we refactored it out? 
# Or we can just run a sim and check 'results' for 'bet' field?
# Simulator.results currently stores {pnl, true_count}. We usually don't store bet size.
# Wait, let's update Simulator to store 'bet' in results to make verification easier?
# Actually, pnl/result ~ bet size. Win = 1.5 bet, etc.
# But clearer to just unit test logic.
# I will make a MockSimulator that inherits and overrides deal/mechanics to just test betting calculation?
# Or easier: Refactor betting calc into a method `calculate_bet(running_count, decks_remaining)` in Simulator and test THAT.

# Actually, I'll update Simulator to have a `get_bet(true_count)` method for testability if I can.
# But avoiding big refactors. I'll just write a script that instantiates Simulator and calls the bet logic block?
# No, it's inside run().
# I will rely on reading the code or doing a short Sim run where I check correlation?
# Let's adding `bet` to the results dict in Simulator first. It's useful for analytics anyway.

