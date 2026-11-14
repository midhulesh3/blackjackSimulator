
import numpy as np
from deck import Deck
from card import Card

class Simulator:
    def __init__(self, rules, strategy, num_simulations=1000):
        self.rules = rules
        self.strategy = strategy
        self.num_simulations = num_simulations
        
        # Stats
        self.results = [] # List of tuples/dicts per hand: (Outcome, PnL, RunningCount, TrueCount)
        self.bankroll_history = []
        self.current_bankroll = rules.get('bankroll', 10000)
        self.initial_bankroll = self.current_bankroll
        
        # Performance
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.blackjacks = 0
        self.total_wagered = 0
        
        # Game State
        self.deck = None
        self.running_count = 0
        self.hands_played = 0

    @property
    def count_imbalance(self):
        """Sum of the counting system's tags over one 52-card deck (0 for balanced counts
        like Hi-Lo, +4 for KO). Cached per strategy."""
        if not hasattr(self, '_count_imbalance'):
            ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
            self._count_imbalance = 4 * sum(self.strategy.get_count_value(Card(r, '')) for r in ranks)
        return self._count_imbalance

    @property
    def true_count(self):
        if not hasattr(self, 'deck') or not self.deck: return 0
        rem = self.deck.decks_remaining
        if rem <= 0:
            return 0
        rc = self.running_count
        # Unbalanced counts (KO, unbalanced Custom) drift by `imbalance` per deck dealt even
        # in a neutral shoe. Remove that expected drift before converting to a true count,
        # otherwise the TC climbs steadily through every shoe and the bettor over-bets.
        imbalance = self.count_imbalance
        num_decks = getattr(self.deck, 'num_decks', None)
        if imbalance and num_decks:
            decks_dealt = num_decks - len(self.deck.cards) / 52.0
            rc -= imbalance * decks_dealt
        return rc / rem

    def update_count(self, card):
        val = self.strategy.get_count_value(card)
        self.running_count += val

    def calculate_bet(self):
        bet_strategy = self.rules.get('betting_strategy', 'Flat')
        min_bet = self.rules.get('min_bet', 10)
        tc = self.true_count
        
        bet = min_bet
        if bet_strategy == 'Flat':
            bet = min_bet
        elif bet_strategy == 'Linear':
            ramp_start = self.rules.get('ramp_start', 1)
            ramp_end = self.rules.get('ramp_end', 5)
            max_bet = min_bet * self.rules.get('max_spread', 10)
            
            if tc < ramp_start:
                bet = min_bet
            elif tc >= ramp_end:
                bet = max_bet
            else:
                slope = (max_bet - min_bet) / (ramp_end - ramp_start)
                additional = (tc - ramp_start) * slope
                bet = min_bet + additional
                
        elif bet_strategy == 'Custom':
            b_map = self.rules.get('custom_bet_map', {}) or {}
            # Parse keys once into floats (JSON keys are strings such as "1", "1.0", "-2")
            thresholds = sorted(((float(k), float(v)) for k, v in b_map.items()),
                                key=lambda kv: kv[0], reverse=True)
            for k, mult in thresholds:
                if tc >= k:
                    bet = min_bet * mult
                    break
                    
        return max(min_bet, int(bet))

    def setup_simulation(self):
        self.deck = Deck(num_decks=self.rules.get('decks', 6), 
                        penetration=self.rules.get('penetration', 0.75))
        self.running_count = 0
        self.hands_played = 0
        self.bankroll_history = [self.current_bankroll]
        self.wins = 0
        self.losses = 0
        self.pushes = 0
        self.blackjacks = 0
        self.total_wagered = 0
        self.results = []
        
    def deal_card(self):
        """Deal a card, reshuffling if the shoe is exhausted mid-round.

        With high penetration and few decks the shoe can run dry in the middle of a
        round; Deck.deal() would return None and crash later."""
        if not self.deck.cards:
            self.deck.shuffle()
            self.running_count = 0
        return self.deck.deal()

    def check_shuffle(self):
        if self.deck.needs_shuffle:
            self.deck.shuffle()
            self.running_count = 0

    def handle_insurance(self, dealer_hand, bet):
        insurance_pnl = 0
        if dealer_hand['cards'][0].rank == 'A' and self.rules.get('insurance_allowed', True):
            # Check funds for insurance
            if self.rules.get('stop_on_ruin', False):
                 # Committed is just the main bet right now (no splits yet)
                 if (self.current_bankroll - bet) < (bet * 0.5):
                     return 0 # Cannot afford insurance
            
            tc = self.true_count
            if self.strategy.should_take_insurance(tc):
                ins_bet = bet * 0.5
                d_val = self.calculate_hand_value(dealer_hand['cards'])
                d_bj = (d_val['total'] == 21 and len(dealer_hand['cards']) == 2)
                
                if d_bj:
                    insurance_pnl = ins_bet * 2
                else:
                    insurance_pnl = -ins_bet
        return insurance_pnl

    def process_blackjack(self, p_bj, d_bj, bet, insurance_pnl, dealer_hand, true_count_start):
        self.update_count(dealer_hand['cards'][1])
        
        round_pnl = 0
        if p_bj and d_bj:
            self.pushes += 1
            round_pnl = 0
        elif p_bj:
            self.wins += 1
            self.blackjacks += 1
            win_amt = bet * 1.5
            self.current_bankroll += win_amt
            round_pnl = win_amt
        else: # d_bj
            self.losses += 1
            self.current_bankroll -= bet
            round_pnl = -bet
            
        round_pnl += insurance_pnl
        if insurance_pnl != 0:
            self.current_bankroll += insurance_pnl
            
        self.total_wagered += bet 
        self.bankroll_history.append(self.current_bankroll)
        self.record_result(round_pnl, true_count_start, bet)
        
    def play_dealer_hand(self, dealer_hand):
        # Reveal hole card
        self.update_count(dealer_hand['cards'][1])
        
        while True:
            d_stats = self.calculate_hand_value(dealer_hand['cards'])
            if d_stats['total'] >= 17:
                if d_stats['total'] == 17 and d_stats['soft'] and self.strategy.dealer_hits_soft_17:
                    # Hit S17
                    pass
                else:
                    break
            
            new_card = self.deal_card()
            dealer_hand['cards'].append(new_card)
            self.update_count(new_card)

    @staticmethod
    def get_base_bet(hand):
        """Original wager unit for a hand (free hands have bet == 0)."""
        if 'base_bet' in hand:
            return hand['base_bet']
        return hand['bet'] if hand['bet'] > 0 else hand.get('free_bet', 0)

    def perform_split(self, current_hand, active_hands, is_split_ace, is_free=False):
        # Create new hand
        unit = self.get_base_bet(current_hand)
        new_bet = 0 if is_free else unit
        new_free_bet = unit if is_free else 0
        
        new_hand = {
            'cards': [current_hand['cards'].pop(1)], # Take second card from first hand
            'bet': new_bet,
            'free_bet': new_free_bet,
            'base_bet': unit,
            'split_group_id': current_hand.get('split_group_id'),
            'is_split_hand': True,
            'from_split_ace': is_split_ace
        }
        current_hand['is_split_hand'] = True
        current_hand['from_split_ace'] = is_split_ace
        
        # Deal cards (Card 2 for Hand 1, Card 2 for Hand 2)
        c1_new = self.deal_card()
        c2_new = self.deal_card()
        
        current_hand['cards'].append(c1_new)
        new_hand['cards'].append(c2_new)
        
        self.update_count(c1_new)
        self.update_count(c2_new)
        
        # DFS Order: Play new_hand (Hand 2), then continue with current_hand (Hand 1)?
        # Wait. "Split -> Hand 1, Hand 2".
        # If I pop `current_hand` (Hand 1), then I should process it.
        # But `current_hand` logic continues in the calling loop.
        # So I insert `new_hand` (Hand 2) to the queue.
        # Queue: [Hand 2, Hand 3...]
        # Current Hand 1 is active.
        # Wait, usually split hands are played sequentially.
        # If I want to play Hand 1 NOW, I continue the loop.
        # Hand 2 is queued.
        # active_hands.insert(0, new_hand) means Hand 2 is next. Correct.
        active_hands.insert(0, new_hand)

    def process_player_turn(self, player_hand, dealer_up_card):
        active_hands = [player_hand]
        finished_hands = []
        
        while active_hands:
            current_hand = active_hands.pop(0)
            
            # Handle split ace stand logic
            is_split_ace = current_hand.get('from_split_ace', False)
            if is_split_ace and len(current_hand['cards']) >= 2:
                 can_hit_ace = self.rules.get('hit_split_aces', False)
                 can_resplit = self.rules.get('resplit_aces', False)
                 # Pair Check
                 if not can_hit_ace:
                     # Check if it's a pair of Aces again?
                     is_pair_aces = (current_hand['cards'][0].rank == 'A' and current_hand['cards'][1].rank == 'A')
                     if not (can_resplit and is_pair_aces):
                         current_hand.update(self.calculate_hand_value(current_hand['cards']))
                         finished_hands.append(current_hand)
                         continue
            
            # Flag to track if we should finish this hand (add to results)
            # or if it went back to queue (Split)
            hand_finished = True
            
            while True:
                hand_info = self.calculate_hand_value(current_hand['cards'])
                current_hand.update(hand_info)
                
                if hand_info['total'] > 21:
                    break # Bust
                
                # Calculate committed funds to verify Double/Split affordability
                committed_funds = current_hand['bet']
                for h in active_hands: committed_funds += h['bet']
                for h in finished_hands: committed_funds += h['bet']
                
                available_funds = self.current_bankroll - committed_funds
                stop_ruin = self.rules.get('stop_on_ruin', False)
                
                # Check options
                can_split = (hand_info['is_pair'] and len(current_hand['cards']) == 2)
                if can_split:
                     if is_split_ace and not self.rules.get('resplit_aces', False):
                         can_split = False
                     if self.rules.get('max_hands', 4) <= (len(finished_hands) + len(active_hands) + 1):
                         can_split = False
                     # Stop on Ruin Check for Split
                     if stop_ruin:
                         # Paid split requires an equal bet; Free Bet splits (non-10 pairs) are free
                         free_split = (self.strategy.variant == 'FreeBet' and current_hand['cards'][0].value != 10)
                         split_cost = 0 if free_split else self.get_base_bet(current_hand)
                         if available_funds < split_cost:
                             can_split = False
                
                can_double = (len(current_hand['cards']) == 2)
                if current_hand.get('is_split_hand') and not self.rules.get('das', True):
                    can_double = False
                if is_split_ace and not self.rules.get('hit_split_aces', False):
                     can_double = False
                # Stop on Ruin Check for Double
                if stop_ruin and can_double:
                    free_double = (self.strategy.variant == 'FreeBet' and not hand_info['soft']
                                   and hand_info['total'] in [9, 10, 11])
                    if not free_double and available_funds < current_hand['bet']:
                        can_double = False
                     
                can_surrender = (len(current_hand['cards']) == 2 and 
                                 not current_hand.get('is_split_hand') and 
                                 self.rules.get('surrender_allowed', False))
                
                
                tc = self.true_count
                is_free_hand = (current_hand['bet'] == 0 and current_hand.get('free_bet', 0) > 0)
                action = self.strategy.get_action(current_hand, dealer_up_card, tc, 
                                                can_split, can_double, can_surrender,
                                                is_free_hand=is_free_hand)
                
                if is_split_ace and not self.rules.get('hit_split_aces', False) and action != 'Split':
                    # Split aces receive exactly one card (unless resplit); e.g. A,A when
                    # resplitting is blocked by max_hands must stand, not hit.
                    action = 'Stand'

                if action == 'Hit':
                    new_card = self.deal_card()
                    current_hand['cards'].append(new_card)
                    self.update_count(new_card)
                elif action == 'Stand':
                    break
                elif action == 'Double':
                    is_free = False
                    if self.strategy.variant == 'FreeBet':
                         # Free Double on Hard 9, 10, 11
                         h_total = current_hand['total']
                         if not current_hand['soft'] and h_total in [9, 10, 11]:
                             is_free = True
                    
                    if is_free:
                        current_hand['free_bet'] = current_hand.get('free_bet', 0) + self.get_base_bet(current_hand)
                    else:
                        current_hand['bet'] *= 2
                        
                    new_card = self.deal_card()
                    current_hand['cards'].append(new_card)
                    self.update_count(new_card)
                    current_hand.update(self.calculate_hand_value(current_hand['cards']))
                    break
                elif action == 'Surrender':
                    current_hand['surrendered'] = True
                    break
                elif action == 'Split':
                    is_free_split = False
                    if self.strategy.variant == 'FreeBet':
                        # Free Split on all pairs except 10, J, Q, K
                        # Card value checking
                        val = current_hand['cards'][0].value
                        if val != 10:
                            is_free_split = True
                            
                    self.perform_split(current_hand, active_hands, 
                                       is_split_ace or (current_hand['cards'][0].rank == 'A'),
                                       is_free=is_free_split)
                    active_hands.insert(0, current_hand) # Re-queue current hand (Hand 1)
                    hand_finished = False # Do not finish yet
                    break
            
            if hand_finished:
                if 'total' not in current_hand:
                     print(f"CRITICAL ERROR: Hand finished without total. Keys: {current_hand.keys()}")
                     print(f"Cards: {current_hand.get('cards')}")
                     # Attempt recovery
                     current_hand.update(self.calculate_hand_value(current_hand['cards']))
                finished_hands.append(current_hand)
            
        return finished_hands

    def settle_round(self, finished_hands, dealer_hand, insurance_pnl, bet, true_count_start):
        d_val = self.calculate_hand_value(dealer_hand['cards'])
        d_total = d_val['total']
        
        round_pnl = insurance_pnl
        if insurance_pnl != 0:
            self.current_bankroll += insurance_pnl
            
        for hand in finished_hands:
            p_total = hand['total']
            hand_bet = hand['bet']
            self.total_wagered += hand_bet
            free_bet_amt = hand.get('free_bet', 0)
            
            pnl_delta = 0
            
            if hand.get('surrendered', False):
                loss = hand_bet * 0.5
                pnl_delta -= loss
                self.losses += 1
            elif p_total > 21:
                pnl_delta -= hand_bet
                self.losses += 1
            elif d_total > 21:
                if self.strategy.variant == 'FreeBet' and d_total == 22:
                    self.pushes += 1
                else:
                    pnl_delta += hand_bet + free_bet_amt
                    self.wins += 1
            elif p_total > d_total:
                pnl_delta += hand_bet + free_bet_amt
                self.wins += 1
            elif p_total < d_total:
                pnl_delta -= hand_bet
                self.losses += 1
            else:
                self.pushes += 1
                
            self.current_bankroll += pnl_delta
            round_pnl += pnl_delta
            
        self.bankroll_history.append(self.current_bankroll)
        self.record_result(round_pnl, true_count_start, bet)

    def play_round(self):
        # Capture TC for records
        start_tc = self.true_count
        
        # 1. Bet
        bet = self.calculate_bet()
        
        # Stop on Ruin Protection: Cap bet at current bankroll
        if self.rules.get('stop_on_ruin', False):
             if self.current_bankroll <= 0:
                 return # Should adhere to loop check, but redundancy is safe
             if bet > self.current_bankroll:
                 bet = int(self.current_bankroll) # All-in logic
                 
             # If bankroll is effectively 0 (e.g. < 1), we might just bet remaining?
             # Logic above handles it.
             # If bet becomes 0?
             if bet <= 0:
                 return # Cannot play with 0
        
        # 2. Deal
        player_hand = {'cards': [self.deal_card(), self.deal_card()], 'bet': bet, 'base_bet': bet, 'split_group_id': self.hands_played}
        dealer_hand = {'cards': [self.deal_card(), self.deal_card()]}
        
        # Pre-count updates (visible cards)
        self.update_count(player_hand['cards'][0])
        self.update_count(player_hand['cards'][1])
        self.update_count(dealer_hand['cards'][0]) # Upcard

        # 3. Insurance & BJ
        p_val = self.calculate_hand_value(player_hand['cards'])
        d_val = self.calculate_hand_value(dealer_hand['cards'])
        p_bj = (p_val['total'] == 21 and len(player_hand['cards']) == 2)
        d_bj = (d_val['total'] == 21 and len(dealer_hand['cards']) == 2)

        insurance_pnl = self.handle_insurance(dealer_hand, bet)
        
        if p_bj or d_bj:
            self.process_blackjack(p_bj, d_bj, bet, insurance_pnl, dealer_hand, start_tc)
            return

        # 4. Player Play
        finished_hands = self.process_player_turn(player_hand, dealer_hand['cards'][0])

        # 5. Dealer Play
        # Check if all busted or surrendered
        all_done = True
        for h in finished_hands:
            if h.get('surrendered'): continue
            if h['total'] <= 21:
                all_done = False
                break
        
        if not all_done:
             self.play_dealer_hand(dealer_hand)
        else:
             # Reveal hole card count anyway
             self.update_count(dealer_hand['cards'][1])

        # 6. Settlement
        self.settle_round(finished_hands, dealer_hand, insurance_pnl, bet, start_tc)

    def run(self):
        self.setup_simulation()
        
        while self.hands_played < self.num_simulations:
            if self.rules.get('stop_on_ruin', False) and self.current_bankroll <= 0:
                break

            self.check_shuffle()
            self.play_round()
            self.hands_played += 1
            
        return self.get_stats()

    def record_result(self, pnl, true_count, bet):
        self.results.append({
            'pnl': pnl,
            'running_count': self.running_count,
            'true_count': true_count,
            'bet': bet
        })

    def calculate_hand_value(self, cards):
        total = 0
        aces = 0
        for card in cards:
            total += card.value
            if card.rank == 'A':
                aces += 1
        
        while total > 21 and aces > 0:
            total -= 10
            aces -= 1
            
        return {
            'total': total,
            'soft': aces > 0,
            'is_pair': (len(cards) == 2 and cards[0].value == cards[1].value) 
        }

    def get_stats(self):
        pnl_array = np.array([r['pnl'] for r in self.results])
        total_pnl = self.current_bankroll - self.initial_bankroll
        
        ev_per_hand = np.mean(pnl_array) if len(pnl_array) > 0 else 0
        variance = np.var(pnl_array) if len(pnl_array) > 0 else 0
        std_dev = np.sqrt(variance)
        
        n0 = (variance / (ev_per_hand**2)) if ev_per_hand != 0 else float('inf')
        
        if variance > 0:
            ror = np.exp(-2 * ev_per_hand * self.initial_bankroll / variance) if ev_per_hand > 0 else 1.0
        else:
            ror = 0.0
            
        return {
            'initial_bankroll': self.initial_bankroll,
            'final_bankroll': self.current_bankroll,
            'total_pnl': total_pnl,
            'total_wagered': self.total_wagered,
            'ev': ev_per_hand,
            'std_dev': std_dev,
            'variance': variance,
            'n0': n0,
            'ror': ror,
            'wins': self.wins,
            'losses': self.losses,
            'pushes': self.pushes,
            'blackjacks': self.blackjacks,
            'bankroll_history': self.bankroll_history,
            'results': self.results
        }

# Helper for Parallel Execution
def run_single_session_batch(rules, strategy_params, num_simulations):
    from strategy import Strategy
    
    strategy = Strategy(
        check_deviations=strategy_params.get('check_deviations', False),
        counting_system=strategy_params.get('counting_system', None),
        counting_params=strategy_params.get('counting_params', {}),
        variant=strategy_params.get('variant', 'Standard'),
        dealer_hits_soft_17=rules.get('dealer_hits_soft_17', False),
        surrender_allowed=rules.get('surrender_allowed', False),
        custom_tables=strategy_params.get('custom_tables', None),
        das=rules.get('das', True)
    )
    
    sim = Simulator(rules, strategy, num_simulations=num_simulations)
    return sim.run()
