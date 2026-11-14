"""Regression tests for bugs found during the bug-hunt pass (see BUG_REPORT.md)."""
import random
import unittest

from card import Card
from simulator import Simulator
from strategy import Strategy
from tests.mocks.deck_mock import MockDeck

BASE_RULES = {'decks': 6, 'min_bet': 10, 'bankroll': 1000, 'das': True, 'max_hands': 4}
FREEBET_RULES = dict(BASE_RULES, dealer_hits_soft_17=True, resplit_aces=True)


def play_turn(sim, cards, dealer_up):
    sim.deck = MockDeck(cards)
    hand = {'cards': [sim.deal_card(), sim.deal_card()], 'bet': 10, 'base_bet': 10}
    return sim.process_player_turn(hand, Card(dealer_up, 'S'))


class TestSimulatorBugfixes(unittest.TestCase):
    def test_blackjack_round_recorded_in_bankroll_history(self):
        sim = Simulator(dict(BASE_RULES), Strategy())
        sim.setup_simulation()
        sim.deck = MockDeck([('A', 'C'), ('K', 'D'), ('6', 'H'), ('10', 'S')])
        sim.play_round()
        self.assertEqual(sim.bankroll_history, [1000, 1015.0])

    def test_custom_bet_map_float_keys(self):
        rules = dict(BASE_RULES, betting_strategy='Custom', custom_bet_map={"1.0": 2, "3": 4})
        sim = Simulator(rules, Strategy())
        sim.setup_simulation()
        sim.running_count = 0
        self.assertEqual(sim.calculate_bet(), 10)
        sim.running_count = 6 * 1.5  # TC 1.5
        self.assertEqual(sim.calculate_bet(), 20)
        sim.running_count = 6 * 3  # TC 3
        self.assertEqual(sim.calculate_bet(), 40)

    def test_shoe_exhaustion_does_not_crash(self):
        random.seed(1)
        rules = dict(BASE_RULES, decks=1, penetration=0.95, bankroll=10 ** 9)
        sim = Simulator(rules, Strategy(), num_simulations=20000)
        stats = sim.run()
        self.assertEqual(len(stats['results']), 20000)

    def test_split_aces_stand_when_resplit_blocked_by_max_hands(self):
        sim = Simulator(dict(BASE_RULES, resplit_aces=True, max_hands=2), Strategy())
        sim.setup_simulation()
        hands = play_turn(sim, [('A', 'C'), ('A', 'D'), ('A', 'H'), ('5', 'S'), ('3', 'C')], '6')
        self.assertEqual([len(h['cards']) for h in hands], [2, 2])

    def test_freebet_resplit_of_free_hand_keeps_stake(self):
        sim = Simulator(dict(FREEBET_RULES), Strategy(variant='FreeBet'))
        sim.setup_simulation()
        # 8,8 vs 6 -> free split. H1 gets 10 (18), H2 gets 8 (8,8 free hand) -> resplit.
        hands = play_turn(sim, [('8', 'C'), ('8', 'D'), ('10', 'S'), ('8', 'H'),
                                ('10', 'C'), ('10', 'H')], '6')
        self.assertEqual(len(hands), 3)
        free_hands = [h for h in hands if h['bet'] == 0]
        self.assertEqual(len(free_hands), 2)
        for h in free_hands:
            self.assertEqual(h['free_bet'], 10)

    def test_freebet_free_double_on_free_hand_adds_stake(self):
        sim = Simulator(dict(FREEBET_RULES), Strategy(variant='FreeBet'))
        sim.setup_simulation()
        # 4,4 vs 6 -> free split. H1: 4+10=14 stand. H2: 4+7=11 (free hand) -> free double.
        hands = play_turn(sim, [('4', 'C'), ('4', 'D'), ('10', 'S'), ('7', 'C'), ('10', 'H')], '6')
        free_hand = [h for h in hands if h['bet'] == 0][0]
        self.assertEqual(len(free_hand['cards']), 3)
        self.assertEqual(free_hand['free_bet'], 20)

    def test_stop_on_ruin_allows_free_split_without_funds(self):
        rules = dict(FREEBET_RULES, bankroll=10, stop_on_ruin=True)
        sim = Simulator(rules, Strategy(variant='FreeBet'))
        sim.setup_simulation()
        hands = play_turn(sim, [('8', 'C'), ('8', 'D'), ('10', 'S'), ('10', 'H')], '6')
        self.assertEqual(len(hands), 2)


if __name__ == '__main__':
    unittest.main()
