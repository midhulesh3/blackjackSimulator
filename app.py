
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json

from simulator import Simulator
from strategy import Strategy

st.set_page_config(page_title="Blackjack Simulator", layout="wide")

import time
import json
import pandas as pd
import numpy as np
import plotly.express as px
from concurrent.futures import ProcessPoolExecutor, as_completed

from card import Card
from deck import Deck
from strategy import Strategy
from simulator import Simulator, run_single_session_batch
st.markdown("Analyze strategies, counting systems, and risk metrics.")

# Sidebar Controls
st.sidebar.header("Simulation Settings")
sim_mode = st.sidebar.radio("Mode", ["Single Session", "Batch Simulation"])

if sim_mode == "Single Session":
    num_simulations = st.sidebar.slider("Number of Hands", min_value=1000, max_value=500000, value=10000, step=1000)
    num_sessions = 1
else:
    num_sessions = st.sidebar.number_input("Number of Sessions", value=100, step=10)
    num_simulations = st.sidebar.number_input("Hands per Session", value=1000, step=1000)

bankroll = st.sidebar.number_input("Initial Bankroll ($)", value=10000, step=1000)
stop_on_ruin = st.sidebar.checkbox("Stop on Ruin (Bankroll <= 0)", value=True)

# ... Game Rules (Decks, etc.) ...
st.sidebar.header("Game Rules")
variant = st.sidebar.selectbox("Game Variant", ["Standard", "FreeBet"])
num_decks = st.sidebar.selectbox("Number of Decks", [1, 2, 4, 6, 8], index=3)
penetration = st.sidebar.slider("Deck Penetration", 0.5, 0.95, 0.75, 0.05)
dealer_s17 = st.sidebar.radio("Dealer Soft 17", ["Stand", "Hit"], index=0)
das = st.sidebar.checkbox("Double After Split (DAS)", value=True)
resplit_aces = st.sidebar.checkbox("Resplit Aces (RSA)", value=False)
hit_split_aces = st.sidebar.checkbox("Hit Split Aces (HSA)", value=False)
surrender_allowed = st.sidebar.checkbox("Allow Late Surrender", value=True)

# ... Strategy & Betting ...
st.sidebar.header("Strategy & Counting")
use_deviations = st.sidebar.checkbox("Use Illustrious 18 Deviations", value=False)
counting_system = st.sidebar.selectbox("Counting System", ["None", "Hi-Lo", "KO", "Custom"])

custom_counts = {}
if counting_system == "Custom":
    default_custom = '{"2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 0, "8": 0, "9": 0, "10": -1, "J": -1, "Q": -1, "K": -1, "A": -1}'
    custom_str = st.sidebar.text_area("Custom Card Values (JSON)", value=default_custom, height=150)
    try:
        custom_counts = json.loads(custom_str)
    except Exception as e:
        st.sidebar.error(f"Invalid JSON: {e}")

st.sidebar.header("Betting")
min_bet = st.sidebar.number_input("Minimum Bet ($)", value=10)
betting_strategy = st.sidebar.selectbox("Betting Strategy", ["Flat", "Linear", "Custom"])

bet_rules = {'betting_strategy': betting_strategy}
if betting_strategy == "Linear":
    st.sidebar.caption("Linear spread from Min Bet to Max Bet based on True Count.")
    ramp_start = st.sidebar.number_input("Ramp Start (True Count)", value=1.0, step=0.5)
    ramp_end = st.sidebar.number_input("Ramp End (True Count)", value=5.0, step=0.5)
    max_spread = st.sidebar.number_input("Max Bet Spread (Multiplier)", value=10, min_value=1)
    
    bet_rules['ramp_start'] = ramp_start
    bet_rules['ramp_end'] = ramp_end
    bet_rules['max_spread'] = max_spread

elif betting_strategy == "Custom":
    st.sidebar.caption("Map True Count to Bet Multiplier.")
    default_map = '{"1": 1, "2": 2, "3": 4, "4": 8, "5": 10}'
    custom_bet_str = st.sidebar.text_area("Bet Map (JSON)", value=default_map, height=100)
    try:
        bet_rules['custom_bet_map'] = json.loads(custom_bet_str)
    except Exception as e:
        st.sidebar.error(f"Invalid JSON: {e}")

# ... (Imports remain same)

# Helper for benchmarking speed
@st.cache_data(show_spinner=False)
def measure_speed(_rules, _strategy_params):
    # Run a small silent sim to gauge speed
    # _arguments to prevent hashing issues if dict order varies? Streamlit handles dicts well.
    sample_size = 5000
    start = time.time()
    
    # Run locally
    strat = Strategy(
        check_deviations=_strategy_params.get('check_deviations', False),
        counting_system=_strategy_params.get('counting_system', None),
        counting_params=_strategy_params.get('counting_params', {}),
        variant=_strategy_params.get('variant', 'Standard'),
        dealer_hits_soft_17=_rules.get('dealer_hits_soft_17', False),
        surrender_allowed=_rules.get('surrender_allowed', False)
    )
    sim = Simulator(_rules, strat, num_simulations=sample_size)
    sim.run()
    
    elapsed = time.time() - start
    if elapsed == 0: return 100000 # Prevent div zero
    return sample_size / elapsed # Hands per second

# ... Sidebar Setup ...

# Prepare estimation params (lightweight)
est_rules = {
    'decks': num_decks, 'penetration': penetration, 'min_bet': min_bet,
    'bankroll': bankroll, 'stop_on_ruin': False,
    'dealer_hits_soft_17': (dealer_s17 == "Hit"), 'das': das, 
    'resplit_aces': resplit_aces, 'hit_split_aces': hit_split_aces,
    'surrender_allowed': surrender_allowed,
    **bet_rules
}
est_strat_params = {
    'check_deviations': use_deviations,
    'counting_system': counting_system if counting_system != "None" else None,
    'counting_params': custom_counts,
    'variant': variant
}

# Calculate Estimate
speed_hps = measure_speed(est_rules, est_strat_params)
total_hands_to_run = num_simulations * (num_sessions if sim_mode == "Batch Simulation" else 1)
est_time_sec = total_hands_to_run / speed_hps

# Display Estimate
if est_time_sec < 60:
    st.sidebar.success(f"Estimated Time: ~{est_time_sec:.1f} sec")
else:
    st.sidebar.warning(f"Estimated Time: ~{est_time_sec/60:.1f} min")
    
# ... Run Button ...

# Run Button
if st.button("Run Simulation"):
    with st.spinner(f"Simulating {num_sessions} session(s)..."):
        # Setup Rules
        rules = {
            'decks': num_decks,
            'penetration': penetration,
            'min_bet': min_bet,
            'bankroll': bankroll,
            'stop_on_ruin': stop_on_ruin,
            'dealer_hits_soft_17': (dealer_s17 == "Hit"),
            'das': das,
            'resplit_aces': resplit_aces,
            'hit_split_aces': hit_split_aces,
            'surrender_allowed': surrender_allowed,
            **bet_rules # Merge betting rules
        }
        
        # Setup Strategy
        strat_system = counting_system if counting_system != "None" else None
        strategy = Strategy(check_deviations=use_deviations, 
                            counting_system=strat_system,
                            counting_params=custom_counts,
                            variant=variant)
        
        if sim_mode == "Single Session":
            # Run Sim
            rules['dealer_hits_soft_17'] = (dealer_s17 == "Hit")
            strategy = Strategy(
                check_deviations=use_deviations, 
                counting_system=counting_system if counting_system != "None" else None, 
                counting_params=custom_counts, 
                variant=variant,
                dealer_hits_soft_17=rules['dealer_hits_soft_17'],
                surrender_allowed=rules.get('surrender_allowed', False)
            )
            sim = Simulator(rules, strategy, num_simulations=num_simulations)
            stats = sim.run()
            
            # Metrics Row 1
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total PnL", f"${stats['total_pnl']:.2f}", delta_color="normal")
            col2.metric("EV / Hand", f"${stats['ev']:.4f}")
            col3.metric("Risk of Ruin", f"{stats['ror']*100:.2f}%")
            n0_disp = f"{int(stats['n0']):,}" if stats['n0'] != float('inf') else "Inf"
            col4.metric("N0 (Hands)", n0_disp)
            
            # Metrics Row 2
            colA, colB, colC, colD = st.columns(4)
            roi = (stats['total_pnl'] / stats['total_wagered']) * 100 if stats['total_wagered'] > 0 else 0.0
            colA.metric("Win Rate", f"{(stats['wins']/num_simulations)*100:.1f}%")
            colB.metric("ROI", f"{roi:.2f}%")
            # Normalized EV for $100 bet: (PnL / Wagered) * 100 = ROI. 
            # User wants "EV per hand... normalized for $100".
            # If I bet $100 every hand, I expect to win $1. This is ROI * 100.
            # Example: ROI 1%. Bet $100 -> Win $1. EV $1.
            # So the value is just ROI. 
            colC.metric("EV per $100 Wagered", f"${roi:.2f}")
            colD.metric("Total Wagered", f"${stats['total_wagered']:,.0f}")
            
            # Check Ruin status
            if stats['final_bankroll'] <= 0:
                st.error("⚠️ RUIN: Bankroll hit $0!")

            # Charts
            st.subheader("Equity Curve")
            history = stats['bankroll_history']
            if len(history) > 5000:
                step = len(history) // 5000
                display_hist = history[::step]
                x_vals = range(0, len(history), step)
            else:
                display_hist = history
                x_vals = range(len(history))
            fig_equity = px.line(x=x_vals, y=display_hist, labels={'x': 'Hand', 'y': 'Bankroll'})
            st.plotly_chart(fig_equity, use_container_width=True)
            
            results_df = pd.DataFrame(stats['results'])
            st.subheader("Distribution of Returns")
            fig_dist = px.histogram(results_df, x="pnl", nbins=50, title="PnL Distribution")
            st.plotly_chart(fig_dist, use_container_width=True)
            
            if counting_system != "None":
                st.subheader("Performance by True Count")
                results_df['TC_Rounded'] = results_df['true_count'].apply(lambda x: round(x))
                results_df = results_df[(results_df['TC_Rounded'] >= -5) & (results_df['TC_Rounded'] <= 10)]
                tc_stats = results_df.groupby('TC_Rounded')['pnl'].mean().reset_index()
                tc_counts = results_df.groupby('TC_Rounded').size().reset_index(name='count')
                fig_tc = px.bar(tc_stats, x='TC_Rounded', y='pnl', title="Average PnL per Hand by True Count")
                st.plotly_chart(fig_tc, use_container_width=True)

        else: # Batch Mode

            session_pnls = []
            final_bankrolls = []
            tot_wagered_all = 0
            tot_pnl_all = 0
            ruined_sessions = 0
            progress_bar = st.progress(0)
            
            # Prepare strategy params
            strategy_params = {
                'check_deviations': use_deviations,
                'counting_system': counting_system if counting_system != "None" else None,
                'counting_params': custom_counts,
                'variant': variant
            }
            
            # Use Parallel Processing with Graceful Cancellation
            completed_count = 0
            executor = ProcessPoolExecutor()
            futures = []
            
            try:
                futures = [executor.submit(run_single_session_batch, rules, strategy_params, num_simulations) for _ in range(num_sessions)]
                
                for future in as_completed(futures):
                    stats = future.result()
                    session_pnls.append(stats['total_pnl'])
                    final_bankrolls.append(stats['final_bankroll'])
                    tot_wagered_all += stats['total_wagered']
                    tot_pnl_all += stats['total_pnl']
                    
                    if stats['final_bankroll'] <= 0:
                        ruined_sessions += 1
                        
                    completed_count += 1
                    progress_bar.progress(completed_count / num_sessions)
            
            except Exception as e:
                # This catches Streamlit's StopException (when user clicks Stop)
                # and generic errors. We MUST shut down the executor immediately.
                st.warning("Simulation Stopped. Terminating workers...")
                executor.shutdown(wait=False, cancel_futures=True)
                raise e # Re-raise to let Streamlit handle the stop UI state logic
            
            finally:
                # Ensure cleanup in all cases
                executor.shutdown(wait=False)

            st.success("Batch Simulation Complete")
            
            # Aggregate Stats
            s_pnls = np.array(session_pnls)
            avg_pnl = np.mean(s_pnls)
            med_pnl = np.median(s_pnls)
            std_pnl = np.std(s_pnls)
            ror_observed = ruined_sessions / num_sessions
            roi_batch = (tot_pnl_all / tot_wagered_all) * 100 if tot_wagered_all > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Avg Session PnL", f"${avg_pnl:.2f}")
            col2.metric("Median PnL", f"${med_pnl:.2f}")
            col3.metric("Ruin Rate", f"{ror_observed*100:.1f}%", help=f"{ruined_sessions} of {num_sessions} sessions ended in total loss")
            col4.metric("EV per $100 Wagered", f"${roi_batch:.2f}")
            
            # Graphs
            st.subheader("Profit/Loss Trend (per Session)")
            # Line chart of Session PnL
            fig_trend = px.line(y=session_pnls, labels={'x': 'Session', 'y': 'Profit/Loss'}, title="PnL per Session")
            fig_trend.add_hline(y=0, line_dash="dash", line_color="red")
            st.plotly_chart(fig_trend, use_container_width=True)
            
            st.subheader("Session Profit/Loss Distribution")
            fig_batch = px.histogram(x=s_pnls, nbins=30, labels={'x': 'Total PnL'}, title="Distribution of Session PnL")
            st.plotly_chart(fig_batch, use_container_width=True)
            
            st.subheader("Aggregate Stats")
            c1, c2 = st.columns(2)
            c1.write(f"**Sessions Run**: {num_sessions}")
            c1.write(f"**Sessions Ruined**: {ruined_sessions} ({ror_observed*100:.1f}%)")
            c1.write(f"**Total Wagered (All Sessions)**: ${tot_wagered_all:,.0f}")
            c1.write(f"**Total PnL (All Sessions)**: ${tot_pnl_all:,.2f}")
            c2.write(f"**Best Session**: ${np.max(s_pnls):.2f}")
            c2.write(f"**Worst Session**: ${np.min(s_pnls):.2f}")
            c2.write(f"**Std Dev**: ${std_pnl:.2f}")

# Strategy Viewer (Always visible or in expander?)
with st.expander("View Strategy Tables"):
    st.subheader(f"{variant} Strategy Tables")
    if use_deviations:
        st.markdown("**Deviations Active:** Illustrious 18")
    
    # We need to instantiate a strategy to get the tables
    # Just reuse logic or instantiate new one
    strat_view = Strategy(
        check_deviations=use_deviations, 
        variant=variant,
        dealer_hits_soft_17=(dealer_s17 == "Hit"),
        surrender_allowed=surrender_allowed
    )
    
    # 1. Hard Totals
    st.caption("Hard Totals")
    # Convert dict to DF for display
    # Keys: Player Total. Values: List of actions for Dealer 2-A
    # Dealer columns: 2 3 4 5 6 7 8 9 10 A
    cols = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'A']
    hard_data = {k: v for k, v in strat_view.hard_strategy.items() if k >= 8} # Show 8+ usually
    df_hard = pd.DataFrame.from_dict(hard_data, orient='index', columns=cols)
    df_hard = df_hard.sort_index(ascending=False)
    st.dataframe(df_hard.style.background_gradient(cmap="RdYlGn", axis=None)) # Simple color map, not perfect for Action codes
    # Better styling: Map codes to colors.
    # H=Green, S=Red, D=Blue, P=Yellow?
    # Streamlit styler applymap
    def color_action(val):
        if 'H' in val: return 'color: green'
        if 'S' in val: return 'color: red'
        if 'D' in val: return 'color: blue'
        if 'P' in val: return 'color: orange'
        return ''
    # st.dataframe(df_hard.style.applymap(color_action)) # applymap deprecated in pandas 2.1+? Uses map now. Check version.
    
    # 2. Soft Totals
    st.caption("Soft Totals")
    soft_data = strat_view.soft_strategy
    df_soft = pd.DataFrame.from_dict(soft_data, orient='index', columns=cols)
    df_soft.index = ["A," + str(i-11) if i<22 else str(i) for i in df_soft.index] # Rename index to A,2 etc?
    # Actually index is Soft Total. 13 = A,2.
    df_soft = df_soft.sort_index(ascending=False)
    st.dataframe(df_soft)
    
    # 3. Pairs
    st.caption("Pairs")
    pair_data = strat_view.pair_strategy
    df_pair = pd.DataFrame.from_dict(pair_data, orient='index', columns=cols)
    # Sort index?
    # Index are strings '2', '3'... '10', 'A'.
    # Custom sort order
    sort_order = ['A', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    df_pair = df_pair.reindex(sort_order)
    st.dataframe(df_pair)
    st.dataframe(df_pair)
