import pandas as pd

class Strategy:
    def __init__(self, check_deviations=False, counting_system=None, counting_params=None, variant='Standard', dealer_hits_soft_17=False, surrender_allowed=False):
        self.check_deviations = check_deviations
        self.counting_system = counting_system # 'Hi-Lo', 'KO', 'Custom'
        self.counting_params = counting_params or {} # Dictionary for custom values
        self.variant = variant # 'Standard' or 'FreeBet'
        self.dealer_hits_soft_17 = dealer_hits_soft_17
        self.surrender_allowed = surrender_allowed
        
        # Determine suffixes
        suffix = "_h17" if dealer_hits_soft_17 else ""
        if self.variant == 'FreeBet':
             # Use specific FreeBet files
             self.hard_strategy = self.load_strategy_csv('strategies/freebet_hard.csv', index_col=0, dtype_idx=int)
             self.soft_strategy = self.load_strategy_csv('strategies/freebet_soft.csv', index_col=0, dtype_idx=int)
             self.pair_strategy = self.load_strategy_csv('strategies/freebet_pair.csv', index_col=0, dtype_idx=str)
        else:
            # Load Standard Strategies
            try:
                self.hard_strategy = self.load_strategy_csv(f'strategies/hard{suffix}.csv', index_col=0, dtype_idx=int)
                if not self.hard_strategy: raise FileNotFoundError 
            except:
                 self.hard_strategy = self.load_strategy_csv('strategies/hard.csv', index_col=0, dtype_idx=int)
                 
            try:
                self.soft_strategy = self.load_strategy_csv(f'strategies/soft{suffix}.csv', index_col=0, dtype_idx=int)
                if not self.soft_strategy: 
                     self.soft_strategy = self.load_strategy_csv('strategies/soft.csv', index_col=0, dtype_idx=int)
            except:
                 self.soft_strategy = self.load_strategy_csv('strategies/soft.csv', index_col=0, dtype_idx=int)
    
            self.pair_strategy = self.load_strategy_csv('strategies/pair.csv', index_col=0, dtype_idx=str)
        
    def load_strategy_csv(self, filepath, index_col, dtype_idx):
        try:
            df = pd.read_csv(filepath)
            # Create dict: Key = Index (converted to dtype), Value = List of actions
            # Columns should be 2,3,4,5,6,7,8,9,10,A which map to index 0-9
            # Verify columns?
            expected_cols = ['2','3','4','5','6','7','8','9','10','A']
            
            # First col is index (e.g. 'Total' or 'Card')
            idx_name = df.columns[0]
            
            strat_dict = {}
            for _, row in df.iterrows():
                key = row[idx_name]
                if dtype_idx == int:
                    key = int(key)
                else:
                    key = str(key)
                
                actions = [row[c] for c in expected_cols]
                strat_dict[key] = actions
            return strat_dict
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return {}
        
    def get_count_value(self, card):
        rank = card.rank
        if self.counting_system == 'Hi-Lo':
            if rank in ['2', '3', '4', '5', '6']:
                return 1
            elif rank in ['7', '8', '9']:
                return 0
            else: # 10, J, Q, K, A
                return -1
        elif self.counting_system == 'KO':
            # 2-7 = +1. 8,9 = 0. 10,A = -1.
            # And it's unbalanced, but we just return point values here.
            if rank in ['2', '3', '4', '5', '6', '7']:
                return 1
            elif rank in ['8', '9']:
                return 0
            else:
                return -1
        elif self.counting_system == 'Custom':
            # Use self.counting_params dictionary
            # Convert rank to int if it's a digit for lookup if needed, creates flexibility
            val = self.counting_params.get(rank)
            if val is not None:
                return val
            # Fallback/try integer keys for number cards
            try:
                if rank.isdigit():
                    return self.counting_params.get(int(rank), 0)
            except:
                pass
            return 0
        return 0

    def get_dealer_index(self, dealer_card):
        # Maps dealer card to 0-9 index for tables
        r = dealer_card.rank
        if r in ['J', 'Q', 'K']:
            return 8 # Value 10 is index 8 (2 is 0) -> 2,3,4,5,6,7,8,9,10,A
                     # Wait. 2=0, 3=1, 4=2, 5=3, 6=4, 7=5, 8=6, 9=7, 10=8, A=9
        elif r == 'A':
            return 9
        else:
            return int(r) - 2

    def get_basic_action(self, hand, dealer_card, can_split=False, can_double=False, can_surrender=False, is_free_hand=False):
        # Basic Strategy Lookup
        dealer_idx = self.get_dealer_index(dealer_card)
        total = hand['total']
        soft = hand['soft']
        
        # Check Pair first
        if hand['is_pair'] and can_split:
            rank = hand['cards'][0].rank
            if rank in ['J', 'Q', 'K']: rank = '10' # Normalize 10s
            action = self.pair_strategy.get(rank, ['H']*10)[dealer_idx]
            if action == 'P': 
                # If is_free_hand, avoid Paid Splits? 
                # Free Bet rules usually cover ALMOST ALL splits as Free. 
                # If it's a Free Split, get_action already returned 'Split'.
                # If we are here, it's a PAID SPLIT (e.g. 10s, or maybe 4s).
                # If is_free_hand, we likely shouldn't Pay to Split.
                if is_free_hand:
                    return 'Stand' if total >= 18 else 'Hit' # Heuristic
                return 'Split'
            
        # Soft Totals
        if soft:
            if total > 21: soft=False
            elif total >= 13 and total <= 21:
                 action_code = self.soft_strategy.get(total, ['S']*10)[dealer_idx]
                 return self.decode_action(action_code, can_double, can_surrender, is_free_hand)
            else:
                 return 'Hit'
        
        # Hard Totals
        if total <= 21:
            # clamp min 4
            t = max(4, total)
            action_code = self.hard_strategy.get(t, ['H']*10)[dealer_idx]
            return self.decode_action(action_code, can_double, can_surrender, is_free_hand)
        
        return 'Stand' 

    def decode_action(self, code, can_double, can_surrender, is_free_hand=False):
        if is_free_hand:
             # Restrict Paid Actions (Double, Surrender)
             # Note: Free Doubles were already handled in get_action before calling this.
             can_double = False 
             can_surrender = False

        if code == 'H': return 'Hit'
        if code == 'S': return 'Stand'
        if code == 'D': return 'Double' if can_double else 'Hit'
        if code == 'Ds': return 'Double' if can_double else 'Stand'
        if code == 'Dh': return 'Double' if can_double else 'Hit'
        # Surrender codes
        if code == 'Rh': return 'Surrender' if (can_surrender and self.surrender_allowed) else 'Hit'
        if code == 'Rs': return 'Surrender' if (can_surrender and self.surrender_allowed) else 'Stand'
        return 'Hit'

    def should_take_insurance(self, true_count):
        # Hi-Lo Index for Insurance is +3
        if self.counting_system == 'Hi-Lo':
            return true_count >= 3
        # Basic Strategy never takes insurance
        return False

    def get_action(self, hand, dealer_card, true_count=0, can_split=False, can_double=False, can_surrender=False, is_free_hand=False):
        # Free Bet Logic overrides
        if self.variant == 'FreeBet':
            # Free Double on Hard 9, 10, 11 (ALWAYS take this, even on paid hands? Yes.)
            hard_total = hand['total']
            is_soft = hand['soft']
            if can_double and not is_soft and hard_total in [9, 10, 11]:
                 # Strategy: Always take the free double (it's +EV)
                 return 'Double'
            
            # Free Split on all pairs except 10s
            if can_split:
                 card_val = hand['cards'][0].value
                 if card_val != 10: # Free split
                     return 'Split'

        # Check Deviations first if enabled
        # Note: Deviations might suggest a Paid Double. 
        # If is_free_hand, we likely shouldn't take paid deviations either?
        # Let's assume No Paid Actions for Free Hands generally.
        if self.check_deviations:
            dev_action = self.check_index_plays(hand, dealer_card, true_count, can_split, can_double, can_surrender)
            if dev_action:
                # If Free Hand, forbid Paid Doubles/Splits/Surrender?
                # Surrender on Free Hand: You get back... 0? 0 risk -> 0 return. 
                # Actually you can't surrender a Free Hand (it's free).
                if is_free_hand:
                    if dev_action in ['Double', 'Split', 'Surrender']:
                         # Downgrade logic? Or just ignore deviation?
                         pass # Fallthrough to basic strategy (which we will also restrict)
                    else:
                        return dev_action
                else:
                    return dev_action
        
        # Get Basic Action
        action = self.get_basic_action(hand, dealer_card, can_split, can_double, can_surrender)
        
        if is_free_hand and self.variant == 'FreeBet':
            # Downgrade Paid Doubles/Splits/Surrenders
            if action == 'Double':
                 # Determine if D or Ds based on table? 
                 # `get_basic_action` returns resolved action.
                 # We need to know if it was D(Hit) or D(Stand).
                 # Re-lookup or infer?
                 # Actually, `get_basic_action` resolved it.
                 # If it was 'Double', it meant 'Double if allowed, else Hit'.
                 # If it was 'Ds', it meant 'Double if allowed, else Stand'.
                 # Since we returned 'Double', the engine will Double.
                 # We want to force Hit/Stand instead.
                 # We can't differentiate D vs Ds here easily without re-lookup or modification.
                 # Optimization: Pass is_free_hand to get_basic_action?
                 pass 
                 
        return self.get_basic_action(hand, dealer_card, can_split, can_double, can_surrender, is_free_hand=is_free_hand)

    def check_index_plays(self, hand, dealer_card, true_count, can_split, can_double, can_surrender):
        """
        Complete Hi-Lo Index Plays including:
        - Illustrious 18 (most valuable plays)
        - Fab Four (surrender plays)
        - Additional high-value index plays
        
        Returns action if deviation from basic strategy is warranted, else None.
        """
        total = hand['total']
        d_val = dealer_card.value
        is_soft = hand['soft']
        is_pair = hand['is_pair']
        
        # ===================================
        # FAB FOUR SURRENDERS (when available)
        # ===================================
        if can_surrender:
            # 14 vs 10 (Index +3)
            if total == 14 and not is_soft and d_val == 10:
                if true_count >= 3: return 'Surrender'
            
            # 15 vs 9 (Index +2) - separate from I18 15 vs 10
            if total == 15 and not is_soft and d_val == 9:
                if true_count >= 2: return 'Surrender'
            
            # 15 vs A (Index +1 for H17, different for S17)
            if total == 15 and not is_soft and dealer_card.rank == 'A':
                if self.dealer_hits_soft_17:
                    if true_count >= 1: return 'Surrender'
                # S17: basic strategy is Hit, no surrender deviation
            
            # 15 vs 10 (Index +4) - part of I18 but also Fab Four
            if total == 15 and not is_soft and d_val == 10:
                if true_count >= 4: return 'Surrender'
        
        # ===================================
        # ILLUSTRIOUS 18 (ordered by importance)
        # ===================================
        
        # 1. Insurance (Index +3) - handled at game level, not here
        
        # 2. 16 vs 10 (Index 0)
        if total == 16 and not is_soft and d_val == 10:
            return 'Stand' if true_count >= 0 else 'Hit'
        
        # 3. 15 vs 10 (Index +4) 
        if total == 15 and not is_soft and d_val == 10:
            return 'Stand' if true_count >= 4 else 'Hit'
        
        # 4. 10,10 vs 5 (Index +5)
        if is_pair and hand['cards'][0].value == 10 and can_split and d_val == 5:
            if true_count >= 5: return 'Split'
        
        # 5. 10,10 vs 6 (Index +4)
        if is_pair and hand['cards'][0].value == 10 and can_split and d_val == 6:
            if true_count >= 4: return 'Split'
        
        # 6. 10 vs 10 (Index +4)
        if total == 10 and not is_soft and d_val == 10:
            if can_double and true_count >= 4: return 'Double'
        
        # 7. 12 vs 3 (Index +2)
        if total == 12 and not is_soft and d_val == 3:
            return 'Stand' if true_count >= 2 else 'Hit'
        
        # 8. 12 vs 2 (Index +3)
        if total == 12 and not is_soft and d_val == 2:
            return 'Stand' if true_count >= 3 else 'Hit'
        
        # 9. 11 vs A (Index +1) - S17 only
        if total == 11 and dealer_card.rank == 'A' and can_double:
            if not self.dealer_hits_soft_17:  # S17
                if true_count >= 1: return 'Double'
        
        # 10. 9 vs 2 (Index +1)
        if total == 9 and not is_soft and d_val == 2:
            if can_double and true_count >= 1: return 'Double'
        
        # 11. 10 vs A (Index +4)
        if total == 10 and not is_soft and dealer_card.rank == 'A':
            if can_double and true_count >= 4: return 'Double'
        
        # 12. 9 vs 7 (Index +3)
        if total == 9 and not is_soft and d_val == 7:
            if can_double and true_count >= 3: return 'Double'
        
        # 13. 16 vs 9 (Index +5)
        if total == 16 and not is_soft and d_val == 9:
            return 'Stand' if true_count >= 5 else 'Hit'
        
        # 14. 13 vs 2 (Index -1)
        if total == 13 and not is_soft and d_val == 2:
            if true_count < -1: return 'Hit'
        
        # 15. 12 vs 4 (Index 0)
        if total == 12 and not is_soft and d_val == 4:
            if true_count < 0: return 'Hit'
        
        # 16. 12 vs 5 (Index -2)
        if total == 12 and not is_soft and d_val == 5:
            if true_count < -2: return 'Hit'
        
        # 17. 12 vs 6 (Index -1)
        if total == 12 and not is_soft and d_val == 6:
            if true_count < -1: return 'Hit'
        
        # 18. 13 vs 3 (Index -2)
        if total == 13 and not is_soft and d_val == 3:
            if true_count < -2: return 'Hit'
        
        # ===================================
        # ADDITIONAL VALUABLE INDEX PLAYS
        # ===================================
        
        # 16 vs A (Index +5)
        if total == 16 and not is_soft and dealer_card.rank == 'A':
            return 'Stand' if true_count >= 5 else 'Hit'
        
        # 15 vs A (Index +5)
        if total == 15 and not is_soft and dealer_card.rank == 'A':
            return 'Stand' if true_count >= 5 else 'Hit'
        
        # 14 vs 2 (Index +3)
        if total == 14 and not is_soft and d_val == 2:
            if true_count >= 3: return 'Stand'
        
        # 11 vs 10 (Index -2) - hit instead of double in bad counts
        if total == 11 and not is_soft and d_val == 10:
            if can_double and true_count < -2: return 'Hit'
        
        # 10 vs 9 (Index -2)
        if total == 10 and not is_soft and d_val == 9:
            if can_double and true_count < -2: return 'Hit'
        
        # 9,9 vs 7 (Index +3)
        if is_pair and hand['cards'][0].value == 9 and can_split and d_val == 7:
            if true_count >= 3: return 'Split'
        
        # 9,9 vs A (Index +3)
        if is_pair and hand['cards'][0].value == 9 and can_split and dealer_card.rank == 'A':
            if true_count >= 3: return 'Split'
        
        # Soft 19 vs 6 (Index +1) - H17 games
        if is_soft and total == 19 and d_val == 6:
            if self.dealer_hits_soft_17 and can_double:
                if true_count >= 1: return 'Double'
        
        # Soft 18 vs 2 (Index +1)
        if is_soft and total == 18 and d_val == 2:
            if can_double and true_count >= 1: return 'Double'
            
        # Soft 18 vs A (Index +1)
        if is_soft and total == 18 and dealer_card.rank == 'A':
            if true_count >= 1: return 'Hit'  # Hit instead of stand in positive counts
        
        return None 
