# Blackjack Strategy Simulator

A professional-grade Blackjack simulation engine with Streamlit UI, capable of simulating millions of hands to analyze counting systems, betting strategies, and rule variations.

## Features
- **Accurate Simulation**: Core engine verified against theoretical EV (House Edge -0.37% to -0.66%).
- **Card Counting**: Supports Hi-Lo, Ko, Hi-Opt I/II, Omega II, and more.
- **Betting Strategies**: Flat, Linear, and Custom betting ramps.
- **Rule Variations**: S17/H17, DAS, RSA, Surrender, Deck Penetration.
- **Interactive Dashboard**: Visualizes Bankroll, EV, and Drawdown.

## Installation

1. **Clone the repository**:
   ```bash
   git clone git@github.com:midhulesh3/blackjackSimulator.git
   cd blackjackSimulator
   ```

2. **Create and Activate Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the App
Launch the interactive web interface:
```bash
streamlit run app.py
```

### Run Verification Tests
Verify house edge against the exact calculator (`exact_ev.py`, infinite-deck probability recursion
that plays the same `Strategy` with the same rules as the simulator):
```bash
python3 -m unittest tests.test_system_ev -v
```
*Checks: (1) exact EV of the shipped strategy for S17, H17, no-DAS, RSA/HSA and Free Bet is pinned to 0.0001%;
(2) implied rule effects (S17, DAS, late surrender) match published values; (3) a seeded infinite-deck
simulation agrees with the exact value within 4 standard errors. Deterministic, ~10s.*

To compute the exact house edge for your own rules and strategy:
```python
from exact_ev import exact_house_edge
from strategy import Strategy
exact_house_edge(Strategy(dealer_hits_soft_17=True, surrender_allowed=True),
                 {'das': True, 'surrender_allowed': True, 'max_hands': 4})   # -> -0.0063 (-0.63%)
```

The legacy script `python3 test_system_ev.py` (repo root) runs a 5M-hand 6-deck simulation for a
rough comparison with published figures (±0.05% noise per run).

### Run Unit Tests
Execute the full test suite for regression testing:
```bash
python3 -m unittest discover tests
```
*Note: A git pre-push hook is installed to automatically run these tests before any push.*

## Structure
- `simulator.py`: Core game engine (refactored).
- `strategy.py`: Strategy lookup and counting logic.
- `app.py`: Streamlit frontend.
- `strategies/`: CSV files defining Basic Strategy tables.
- `tests/`: Unit tests for critical logic.

## Credits
Based on modern Blackjack theory (Ill18, Fab4) and open-source verification tools.
