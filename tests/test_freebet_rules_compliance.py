import unittest
from simulator import Simulator
from strategy import Strategy
from card import Card
from tests.mocks.deck_mock import MockDeck

class TestFreeBetRulesCompliance(unittest.TestCase):
    def get_freebet_rules(self):
        return {
            'decks': 6,
            'dealer_hits_soft_17': True,
            'resplit_aces': True, # Key Rule Check
            'das': True,
            'surrender_allowed': False, # Key Rule Check
            'min_bet': 10,
            'max_hands': 4,
            'blackjacks_pay_3_2': True # Implicit in sim
        }

    def test_payout_free_double_win(self):
        # Rule: Player wins, gets back original + winnings equal to double.
        # Implies Profit = 2 * Original.
        # My Code checks: pnl_delta += hand_bet + free_bet.
        # Scenario: Bet 10. Free Double. Win.
        
        rules = self.get_freebet_rules()
        sim = Simulator(rules, Strategy(variant='FreeBet'))
        sim.setup_simulation()
        
        # Hand: Hard 11 (6,5). Dealer: 6.
        # Player Doubles (Free). Gets K (21). Dealer 17.
        cards = [
            ('6','C'), ('5','D'), ('6','H'), ('10','S'), # Upcard 6. Hole 10.
            ('K','C'), # Player Double Card
            # Dealer stands on 16? No hit to 17?
            # Dealer (6, 10). 16. Hits. 
             ('Ace','D') # 17 (Soft). Matches rule "Dealer hits soft 17"
            # Wait, if Dealer hits soft 17 (Ace), gets... say 10 -> Hard 17? Or 4 -> 21?
            # Let's give Dealer a bust card. ('10'). 27.
        ]
        
        # Dealer Sequence:
        # P: 11. D: 6.
        # P Free Double -> Gets K (21).
        # D Turn: 6, 10 (16). Hit.
        # Card 4: Give Dealer 10 -> 26 Bust.
        # Result: Player Wins.
        
        deck_cards = [
           ('6','C'), ('5','D'), ('6','H'), ('10','S'),
           ('K','C'), # Player
           ('10','D') # Dealer Hit
        ]
        
        sim.deck = MockDeck(deck_cards)
        sim.play_round()
        
        # Check PnL
        # Bet 10.
        # Profit should be 20. (Original 10 safe + 20 Winnings).
        # Wait. "Gets back original + winnings equal to double".
        # If I enter with 1000. Bet 10. Bankroll 1000.
        # Win. Get back 10? No, keeping 10 is "getting back". 
        # Plus Winnings (20).
        # Final Bankroll 1020.
        # PnL recorded should be +20 ?
        # Or +30 if start from "Bet Deducted"?
        # My Sim does NOT deduct bet.
        # So PnL = Change.
        # Change = +20.
        
        res = sim.results[0]
        self.assertEqual(res['pnl'], 20.0, "Free Double Win should profit 2x Bet")

    def test_payout_free_split_win(self):
        # Rule: Free Split. Winning free hand button replaced by real chips.
        # Scenario: 8,8 vs 6. Free Split.
        # H1 Wins. H2 (Free) Wins.
        # Bet 10.
        # H1 Profit: 10.
        # H2 Profit: 10.
        # Total Profit: 20.
        
        rules = self.get_freebet_rules()
        sim = Simulator(rules, Strategy(variant='FreeBet'))
        sim.setup_simulation()
        
        # P: 8,8. D: 6.
        # Split.
        # H1: 8 + 10 = 18. Stand.
        # H2: 8 + 10 = 18. Stand.
        # D: 6+10=16. Hit -> 10 = 26 Bust.
        
        deck_cards = [
            ('8','C'), ('8','D'), ('6','H'), ('10','H'),
            ('10','S'), # H1
            ('10','C'), # H2
            ('10','D')  # Dealer Hit
        ]
        
        sim.deck = MockDeck(deck_cards)
        sim.play_round()
        
        res = sim.results[0]
        # PnL should be 20
        self.assertEqual(res['pnl'], 20.0, "Free Split Dual Win should profit 2x Bet")

    def test_resplit_aces_allowed(self):
        # Rule: Re-split pairs up to four hands, including aces.
        # Scenario: A, A vs 6.
        # Split -> A, (new A). A, (new 10).
        # Hand 1 is A,A. Should Resplit.
        
        rules = self.get_freebet_rules() # resplit_aces=True
        sim = Simulator(rules, Strategy(variant='FreeBet'))
        sim.setup_simulation()
        
        # P: A, A. D: 6.
        # Split.
        # H1: A + A. -> Resplit.
        #   H1a: A + 10 -> 21.
        #   H1b: A + 10 -> 21.
        # H2: A + 10 -> 21.
        # Total 3 Hands.
        # D: 6, 10, 10 (Bust).
        
        deck_cards = [
            ('A','C'), ('A','D'), ('6','H'), ('10','H'),
            ('A','H'), # H1 dealt A -> Resplit!
            ('10','C'), # H1a dealt 10
            ('10','S'), # H1b dealt 10
            ('10','D'), # H2 dealt 10.
            ('10','C')  # Dealer Hit
        ]
        
        sim.deck = MockDeck(deck_cards)
        sim.play_round()
        
        # Check we have 3 results?
        # Sim aggregates round pnl.
        # 3 Hands. All Win.
        # Profits:
        # H1a (From Split 1 -> Resplit): Bet 10. Win 10.
        # H1b (From Resplit): Bet 10? Wait. Free Split?
        # A,A is Free Split.
        # Resplit A,A is also Free Split?
        # Usually yes.
        # If all Free, then:
        # H1 (Original Bet 10). Split -> H1(10), H2(Free).
        # H1 (10) is A,A. Resplit -> H1a(10), H1b(Free).
        # So: H1a(10), H1b(Free), H2(Free).
        # All Win.
        # Profit: 10 + 10 + 10 = 30.
        
        res = sim.results[0]
        self.assertEqual(res['pnl'], 30.0, "Should allow resplitting aces and payout correctly")

if __name__ == '__main__':
    unittest.main()
