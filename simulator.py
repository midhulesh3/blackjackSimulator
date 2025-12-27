
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
    def true_count(self):
        if not hasattr(self, 'deck') or not self.deck: return 0
        rem = self.deck.decks_remaining
        return self.running_count / rem if rem > 0 else 0

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
            b_map = self.rules.get('custom_bet_map', {})
            sorted_keys = sorted([float(k) for k in b_map.keys()], reverse=True)
            for k in sorted_keys:
                if tc >= k:
                    bet = min_bet * b_map[str(int(k)) if k.is_integer() else str(k)] 
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
        
    def check_shuffle(self):
        if self.deck.needs_shuffle:
            self.deck.shuffle()
            self.running_count = 0

    def handle_insurance(self, dealer_hand, bet):
        insurance_pnl = 0
        if dealer_hand['cards'][0].rank == 'A' and self.rules.get('insurance_allowed', True):
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
            
            new_card = self.deck.deal()
            dealer_hand['cards'].append(new_card)
            self.update_count(new_card)

    def perform_split(self, current_hand, active_hands, is_split_ace, is_free=False):
        # Create new hand
        new_bet = 0 if is_free else current_hand['bet']
        new_free_bet = current_hand['bet'] if is_free else 0
        
        new_hand = {
            'cards': [current_hand['cards'].pop(1)], # Take second card from first hand
            'bet': new_bet,
            'free_bet': new_free_bet,
            'split_group_id': current_hand.get('split_group_id'),
            'is_split_hand': True,
            'from_split_ace': is_split_ace
        }
        current_hand['is_split_hand'] = True
        current_hand['from_split_ace'] = is_split_ace
        
        # Deal cards (Card 2 for Hand 1, Card 2 for Hand 2)
        c1_new = self.deck.deal()
        c2_new = self.deck.deal()
        
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
                
                # Check options
                can_split = (hand_info['is_pair'] and len(current_hand['cards']) == 2)
                if can_split:
                     if is_split_ace and not self.rules.get('resplit_aces', False):
                         can_split = False
                     if self.rules.get('max_hands', 4) <= (len(finished_hands) + len(active_hands) + 1):
                         can_split = False
                
                can_double = (len(current_hand['cards']) == 2)
                if current_hand.get('is_split_hand') and not self.rules.get('das', True):
                    can_double = False
                if is_split_ace and not self.rules.get('hit_split_aces', False):
                     can_double = False
                     
                can_surrender = (len(current_hand['cards']) == 2 and 
                                 not current_hand.get('is_split_hand') and 
                                 self.rules.get('surrender_allowed', False))
                
                
                tc = self.true_count
                is_free_hand = (current_hand['bet'] == 0 and current_hand.get('free_bet', 0) > 0)
                action = self.strategy.get_action(current_hand, dealer_up_card, tc, 
                                                can_split, can_double, can_surrender,
                                                is_free_hand=is_free_hand)
                
                if action == 'Hit':
                    new_card = self.deck.deal()
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
                        current_hand['free_bet'] = current_hand.get('free_bet', 0) + current_hand['bet']
                    else:
                        current_hand['bet'] *= 2
                        
                    new_card = self.deck.deal()
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
        
        # 2. Deal
        player_hand = {'cards': [self.deck.deal(), self.deck.deal()], 'bet': bet, 'split_group_id': self.hands_played}
        dealer_hand = {'cards': [self.deck.deal(), self.deck.deal()]}
        
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
        surrender_allowed=rules.get('surrender_allowed', False)
    )
    
    sim = Simulator(rules, strategy, num_simulations=num_simulations)
    return sim.run()
