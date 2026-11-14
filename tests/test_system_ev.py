"""House-edge verification against the exact (infinite-deck) calculator in exact_ev.py.

This replaces the old check (50k simulated 6-deck hands vs a published figure with +/-1.0% tolerance).
That check had ~0.5% noise per run, so it could only catch errors larger than ~1% and failed at
random about 5% of the time.

1. TestExactHouseEdge: deterministic. Pins the exact EV of the shipped strategy tables for each
   game, so any change to tables, strategy logic or rule handling that moves EV by more than 0.0001%
   fails. If you change strategy intentionally, re-run exact_ev and update the pinned values.
2. TestRuleEffects: the rule effects implied by the calculator must match published values.
3. TestSimulatorMatchesExact: the simulator itself, on a seeded infinite deck, must land within
   4 standard errors of the exact value. Deterministic (fixed seed), so it never flakes.
"""
import math
import unittest

from exact_ev import exact_house_edge
from simulator import Simulator
from strategy import Strategy
from tests.mocks.infinite_deck import InfiniteDeck

BASE = {'das': True, 'surrender_allowed': True, 'resplit_aces': False, 'hit_split_aces': False, 'max_hands': 4}

# name: (Strategy kwargs, rules, pinned exact house edge in %)
GAMES = {
    'S17 DAS LS': (dict(dealer_hits_soft_17=False, surrender_allowed=True), BASE, -0.427037),
    'H17 DAS LS': (dict(dealer_hits_soft_17=True, surrender_allowed=True), BASE, -0.630064),
    'S17 DAS': (dict(dealer_hits_soft_17=False), dict(BASE, surrender_allowed=False), -0.512547),
    'H17 noDAS LS': (dict(dealer_hits_soft_17=True, surrender_allowed=True, das=False),
                     dict(BASE, das=False), -0.773462),
    'S17 DAS LS RSA HSA': (dict(dealer_hits_soft_17=False, surrender_allowed=True),
                           dict(BASE, resplit_aces=True, hit_split_aces=True), -0.163618),
    'Free Bet': (dict(variant='FreeBet', dealer_hits_soft_17=True),
                 dict(BASE, surrender_allowed=False, resplit_aces=True), -0.995407),
}

_cache = {}


def exact(name):
    if name not in _cache:
        skw, rules, _ = GAMES[name]
        _cache[name] = 100 * exact_house_edge(Strategy(**skw), rules)
    return _cache[name]


class TestExactHouseEdge(unittest.TestCase):
    def test_pinned_values(self):
        for name, (_, _, pinned) in GAMES.items():
            with self.subTest(game=name):
                self.assertAlmostEqual(exact(name), pinned, delta=1e-4,
                                       msg=f"{name}: exact EV changed; update pin if intentional")


class TestRuleEffects(unittest.TestCase):
    """Published rule effects (approx.): S17 vs H17 ~0.20-0.22%, DAS ~0.14%, late surrender ~0.08%."""

    def test_s17_vs_h17(self):
        self.assertAlmostEqual(exact('S17 DAS LS') - exact('H17 DAS LS'), 0.21, delta=0.03)

    def test_late_surrender(self):
        self.assertAlmostEqual(exact('S17 DAS LS') - exact('S17 DAS'), 0.08, delta=0.03)

    def test_double_after_split(self):
        self.assertAlmostEqual(exact('H17 DAS LS') - exact('H17 noDAS LS'), 0.14, delta=0.03)


class InfiniteDeckSimulator(Simulator):
    def __init__(self, *args, seed, **kwargs):
        super().__init__(*args, **kwargs)
        self.seed = seed

    def setup_simulation(self):
        super().setup_simulation()
        self.deck = InfiniteDeck(self.seed)


class TestSimulatorMatchesExact(unittest.TestCase):
    HANDS = 300_000

    def check(self, name, seed):
        skw, rules, _ = GAMES[name]
        sim_rules = dict(rules, dealer_hits_soft_17=skw.get('dealer_hits_soft_17', False), min_bet=1,
                         betting_strategy='Flat', bankroll=10 ** 12, stop_on_ruin=False)
        sim = InfiniteDeckSimulator(sim_rules, Strategy(**skw), num_simulations=self.HANDS, seed=seed)
        stats = sim.run()
        pnl = [r['pnl'] for r in stats['results']]
        n = len(pnl)
        mean = sum(pnl) / n
        se = math.sqrt(sum((x - mean) ** 2 for x in pnl) / (n - 1) / n)
        z = (100 * mean - exact(name)) / (100 * se)
        print(f"\n{name}: simulated {100*mean:+.3f}% +/- {100*se:.3f}% vs exact {exact(name):+.3f}% (z={z:+.2f})")
        self.assertLess(abs(z), 4.0, f"{name}: simulator disagrees with exact EV (z={z:.2f})")

    def test_s17(self):
        self.check('S17 DAS LS', seed=1)

    def test_h17(self):
        self.check('H17 DAS LS', seed=2)

    def test_free_bet(self):
        self.check('Free Bet', seed=3)


if __name__ == '__main__':
    unittest.main()
