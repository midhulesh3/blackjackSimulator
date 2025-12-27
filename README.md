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
Verify the simulator's accuracy against theoretical benchmarks:
```bash
python3 test_system_ev.py
```
*Expected Output: Confirms House Edge is within 0.05% of known values for S17/H17 games.*

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
