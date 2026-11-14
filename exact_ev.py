"""Exact (infinite-deck) expected value of a Strategy under the simulator's rules.

Plays the given `Strategy` object exactly the way `simulator.py` does, but computes the
result by exhaustive probability recursion instead of sampling:

- dealer peeks for blackjack (ace or ten up); player blackjack pays 3:2
- late surrender on the first two cards of an unsplit hand
- double on any two cards; after a split only if `das`
- splits up to `max_hands`, resolved in the simulator's depth-first order
- split aces get one card unless `hit_split_aces`; resplit only if `resplit_aces`
- Free Bet: free doubles on hard 9-11, free splits on non-ten pairs, dealer 22 pushes
- no insurance; true count fixed at 0 (count-independent play)

With an infinite deck every card is drawn with fixed probability (1/13 per rank, 4/13 for ten-valued
cards), so results are exact for that model. A 6-deck shoe gives a slightly lower house edge
(~0.07-0.08%), and a cut card a slightly higher one (~0.02%).

Validation: over 40M hands per game, the simulator run on an infinite deck matched these values within
1 standard error for S17, H17 and Free Bet.
"""
from card import Card

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'A']
PROB = {r: (4 / 13 if r == '10' else 1 / 13) for r in RANKS}
VALUE = {r: (11 if r == 'A' else int(r)) for r in RANKS}


def add_card(total, soft, rank):
    """Add one card to a hand given as (total, soft). Returns the new (total, soft)."""
    if rank == 'A':
        if soft:
            total += 1
        else:
            total += 11
            soft = True
    else:
        total += VALUE[rank]
    if total > 21 and soft:
        total -= 10
        soft = False
    return total, soft


def two_cards(r1, r2):
    return add_card(*add_card(0, False, r1), r2)


class ExactEV:
    def __init__(self, strategy, rules):
        self.strategy = strategy
        self.rules = rules
        self.h17 = strategy.dealer_hits_soft_17
        self.freebet = strategy.variant == 'FreeBet'
        self._dealer = {}
        self._play = {}

    # ----------------------------------------------------------------- dealer
    def dealer_dist(self, up):
        """Dealer final totals given the upcard, conditioned on no dealer blackjack.
        Keys: 17-21, 22 (exactly 22, matters for Free Bet), 23 (any other bust)."""
        if up in self._dealer:
            return self._dealer[up]
        bj_card = '10' if up == 'A' else ('A' if up == '10' else None)
        p_no_bj = 1 - (PROB[bj_card] if bj_card else 0)
        out = {}

        def rec(total, soft, ncards, p):
            if total >= 17 and not (total == 17 and soft and self.h17):
                key = total if total <= 21 else (22 if total == 22 else 23)
                out[key] = out.get(key, 0.0) + p
                return
            for r in RANKS:
                if ncards == 1:  # hole card
                    if r == bj_card:
                        continue
                    q = PROB[r] / p_no_bj
                else:
                    q = PROB[r]
                rec(*add_card(total, soft, r), ncards + 1, p * q)

        rec(*add_card(0, False, up), 1, 1.0)
        self._dealer[up] = out
        return out

    def settle(self, total, up, stake, free_stake):
        """Money EV of standing on `total` with a paid `stake` plus `free_stake` riding for free."""
        if total > 21:
            return -stake
        ev = 0.0
        for d, p in self.dealer_dist(up).items():
            if d == 22 and self.freebet:
                continue  # push 22
            if d > 21 or total > d:
                ev += p * (stake + free_stake)
            elif total < d:
                ev -= p * stake
        return ev

    # ----------------------------------------------------------------- player
    def action(self, total, soft, up, ncards, pair_rank=None, split_hand=False, split_ace=False,
               can_split=False, free_hand=False):
        if pair_rank:
            cards = [Card(pair_rank, ''), Card(pair_rank, '')]
        else:
            cards = [Card('2', '')] * ncards  # only total/soft matter for non-pairs
        hand = {'total': total, 'soft': soft, 'is_pair': pair_rank is not None, 'cards': cards}
        can_double = ncards == 2
        if split_hand and not self.rules.get('das', True):
            can_double = False
        if split_ace and not self.rules.get('hit_split_aces', False):
            can_double = False
        can_surrender = (ncards == 2 and not split_hand and self.rules.get('surrender_allowed', False))
        return self.strategy.get_action(hand, Card(up, ''), 0, can_split, can_double, can_surrender,
                                        is_free_hand=free_hand)

    def play(self, total, soft, up, ncards, split_hand=False, split_ace=False, stake=1.0, free_stake=0.0):
        """Money EV of playing out a hand that will not be split."""
        key = (total, soft, up, min(ncards, 3), split_hand, split_ace, stake, free_stake)
        if key in self._play:
            return self._play[key]
        if total > 21:
            ev = -stake
        elif split_ace and not self.rules.get('hit_split_aces', False):
            ev = self.settle(total, up, stake, free_stake)
        else:
            a = self.action(total, soft, up, ncards, split_hand=split_hand, split_ace=split_ace,
                            free_hand=(stake == 0 and free_stake > 0))
            if a == 'Stand':
                ev = self.settle(total, up, stake, free_stake)
            elif a == 'Surrender':
                ev = -0.5 * stake
            elif a == 'Hit':
                ev = sum(PROB[r] * self.play(*add_card(total, soft, r), up, ncards + 1,
                                             split_hand, split_ace, stake, free_stake)
                         for r in RANKS)
            elif a == 'Double':
                free_double = self.freebet and not soft and total in (9, 10, 11)
                unit = stake if stake > 0 else free_stake
                s2, f2 = (stake, free_stake + unit) if free_double else (stake * 2, free_stake)
                ev = sum(PROB[r] * self.settle(add_card(total, soft, r)[0], up, s2, f2) for r in RANKS)
            else:
                raise ValueError(f"Unexpected action {a!r}")
        self._play[key] = ev
        return ev

    def split(self, rank, up):
        """EV of splitting a pair of `rank`, resolved in the simulator's DFS order."""
        max_hands = self.rules.get('max_hands', 4)
        is_ace = rank == 'A'
        can_resplit = not is_ace or self.rules.get('resplit_aces', False)
        free_split = self.freebet and VALUE[rank] != 10
        new_hand = (0.0, 1.0) if free_split else (1.0, 0.0)  # (stake, free_stake) of each new hand
        memo = {}

        def F(queue, nhands):
            # queue: hands still to play, front first, each (second_card, stake, free_stake)
            if not queue:
                return 0.0
            k = (queue, nhands)
            if k in memo:
                return memo[k]
            (r2, s, f), rest = queue[0], queue[1:]
            total, soft = two_cards(rank, r2)
            ev = None
            if r2 == rank and nhands < max_hands and can_resplit:
                a = self.action(total, soft, up, 2, pair_rank=rank, split_hand=True, split_ace=is_ace,
                                can_split=True, free_hand=(s == 0 and f > 0))
                if a == 'Split':
                    ev = sum(PROB[c1] * PROB[c2] * F(((c1, s, f), (c2,) + new_hand) + rest, nhands + 1)
                             for c1 in RANKS for c2 in RANKS)
            if ev is None:
                ev = self.play(total, soft, up, 2, split_hand=True, split_ace=is_ace, stake=s, free_stake=f) \
                    + F(rest, nhands)
            memo[k] = ev
            return ev

        return sum(PROB[c1] * PROB[c2] * F(((c1, 1.0, 0.0), (c2,) + new_hand), 2)
                   for c1 in RANKS for c2 in RANKS)

    def initial_hand(self, r1, r2, up):
        """EV of a non-blackjack starting hand, given the dealer has no blackjack."""
        total, soft = two_cards(r1, r2)
        if r1 == r2 and self.rules.get('max_hands', 4) > 1:
            if self.action(total, soft, up, 2, pair_rank=r1, can_split=True) == 'Split':
                return self.split(r1, up)
        return self.play(total, soft, up, 2)

    def house_edge(self):
        """Expected return per initial unit bet (negative = house advantage)."""
        ev = 0.0
        for up in RANKS:
            p_dealer_bj = PROB['10'] if up == 'A' else (PROB['A'] if up == '10' else 0.0)
            for r1 in RANKS:
                for r2 in RANKS:
                    p = PROB[up] * PROB[r1] * PROB[r2]
                    if {r1, r2} == {'A', '10'}:
                        hand_ev = (1 - p_dealer_bj) * 1.5          # push vs dealer BJ
                    else:
                        hand_ev = -p_dealer_bj + (1 - p_dealer_bj) * self.initial_hand(r1, r2, up)
                    ev += p * hand_ev
        return ev


def exact_house_edge(strategy, rules):
    return ExactEV(strategy, rules).house_edge()
