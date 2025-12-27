import unittest
from simulator import Simulator
from strategy import Strategy
from tests.mocks.deck_mock import MockDeck

class TestStopOnRuin(unittest.TestCase):
    def test_stop_on_ruin_caps_loss(self):
        # Initial Bankroll: 100
        # Min Bet: 25
        # Bet Strategy: Flat 100 (Overbetting)
        # We want to see if it lets us bet 100 when we only have 100.
        # If we lose, we go to 0. Stopped.
        # But if we have 10 left, and we bet 100?
        
        rules = {
            'decks': 6,
            'min_bet': 50,
            'bankroll': 100,
            'stop_on_ruin': True,
            'betting_strategy': 'Flat',
            # Sim will bet min_bet (50) by default strategy logic if 'Flat', 
            # unless we force the betting logic?
            # 'Flat' strategy in simulator uses `min_bet`.
            # So let's set min_bet = 50.
        }
        
        # We need to simulate a series of losses.
        # Hand 1: Bet 50. Lose. Bankroll 50.
        # Hand 2: Bet 50. Lose. Bankroll 0. -> Stop.
        # Hand 3: Should not happen.
        
        sim = Simulator(rules, Strategy())
        sim.setup_simulation()
        
        # Deck: P(10,10)=20. D(10,A)=BJ. Dealer Wins.
        # Repeat this pattern.
        deck_cards = [
            ('10','C'), ('10','D'), ('10','H'), ('A','H'), # Hand 1 (D BJ)
            ('10','S'), ('10','C'), ('10','D'), ('A','D'), # Hand 2 (D BJ)
            ('10','H'), ('10','S'), ('10','C'), ('A','C')  # Hand 3
        ]
        sim.deck = MockDeck(deck_cards)
        
        sim.run()
        
        print(f"Final Bankroll: {sim.current_bankroll}")
        self.assertGreaterEqual(sim.current_bankroll, 0, "Bankroll passed 0 despite stop_on_ruin (Exact limit case)")

    def test_deep_negative_prevention(self):
        # Scenario: Bankroll 10. Min Bet 20.
        # Standard Sim logic might calculate bet=20.
        # If we play, we bet 20. Lose. Bankroll -10.
        # This is "negative", but is it "deep"?
        # User says "deep negative".
        # Maybe spread betting?
        
        rules = {
            'decks': 6,
            'min_bet': 100,
            'bankroll': 50,
            'stop_on_ruin': True
        }
        sim = Simulator(rules, Strategy())
        sim.setup_simulation()
        
        # 1 Hand. Lose.
        # Expectation: Should we even play if Bankroll < Min Bet?
        # If we play, we bet 100? -> -50.
        # Ideally, we should bet min(100, 50) = 50. -> 0.
        
        deck_cards = [('10','C'), ('10','D'), ('10','H'), ('A','H')]
        sim.deck = MockDeck(deck_cards)
        sim.run()
        
        print(f"Deep Negative Test Final: {sim.current_bankroll}")
        # If logic is "Bet whatever calculate_bet says", it will be -50.
        # If we want to prevent deep negative, we must cap bet.
        
        # Let's Assert that we didn't lose MORE than what we had?
        # i.e. Bankroll shouldn't be negative?
        # Or at least not -MinBet?
        
        # User request: "worst session goes into deep negative".
        # This implies it might be continually playing?
        # No, check break is at top of loop.
        # So it plays at most 1 hand into negative.
        # BUT if bet is HUGE (e.g. Kelly criterion gone wrong or huge spread)?
        
        self.assertGreaterEqual(sim.current_bankroll, -50, "Should not go extremely negative")
        self.assertGreaterEqual(sim.current_bankroll, 0, "Ideally should not go negative at all (Cap bet)")

if __name__ == '__main__':
    unittest.main()
