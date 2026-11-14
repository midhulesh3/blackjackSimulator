# Bug Report — blackjackSim

Branch: `feature/editable-strategy` · Date: 2026-11-14

Before this pass, all 41 existing tests passed; none of the bugs below were covered by them. Each fix
comes with a regression test in `tests/test_bugfixes.py` (15 new tests; suite is now 55 tests, all passing).

## Commits

| Commit | Scope |
|---|---|
| `f453530` | Simulator fixes (#1–#6) |
| `e091a46` | Strategy / basic-strategy table fixes (#7–#11) |
| `6060b83` | Streamlit app fixes (#12–#17) |
| `09b9583` | True count for unbalanced counts (#18) |

## Bugs found and fixed

### Simulator (`simulator.py`)

| # | Severity | Bug | Impact | Fix |
|---|---|---|---|---|
| 1 | High | **Blackjack rounds were not added to `bankroll_history`.** `process_blackjack` returned before the history append in `settle_round`. | The equity curve skipped about 5% of rounds and didn't line up with the hands played. | Append to history in `process_blackjack`. |
| 2 | High (crash) | **Dealing from an empty shoe.** `Deck.deal()` returns `None` when out of cards; with few decks and high penetration (e.g. 1 deck @ 95%) a round can run out mid-hand → `AttributeError: 'NoneType' object has no attribute 'rank'`. | The simulation crashed with settings the UI allows. | New `Simulator.deal_card()` reshuffles if the shoe runs out mid-round (and resets the count). |
| 3 | Medium | **Split aces could be hit.** With RSA on, an A,A split hand that couldn't be resplit (max hands reached) went into the normal loop and hit. | Split aces got 3+ cards, which the rules don't allow. | Split aces that can't be hit are forced to Stand unless they actually resplit. |
| 4 | High | **Free Bet: resplitting a free hand created a $0 hand.** `perform_split` used `current_hand['bet']` as the stake, which is 0 on a free hand. | A free resplit added no free stake, which undervalues the Free Bet game. | Track `base_bet` (the original wager) on each hand and use it for split stakes. |
| 5 | High | **Free Bet: free double on a free hand added $0.** The same `current_hand['bet']` bug in the free-double path. | Free doubles after a free split were worthless. | Use `base_bet` for the free-double stake. |
| 6 | Medium | **Stop-on-ruin blocked free splits and free doubles**, even though they cost nothing. **Custom bet map crashed** (`KeyError`) on keys such as `"1.0"`, because lookup rebuilt the key as `"1"`. | Free Bet play was wrong near ruin; valid JSON crashed the app. | Funds check uses the real cost (0 for free actions); the bet map parses keys to floats once. |

### Strategy (`strategy.py`, `strategies/*.csv`)

| # | Severity | Bug | Impact | Fix |
|---|---|---|---|---|
| 7 | High | **Index plays overrode pair splits.** Deviations are keyed on the total, so 8,8 vs 10 matched "16 vs 10" and returned Stand/Hit before the pair table was checked. The same happened to 8,8 vs 9/A, 6,6 vs 2–6 and 7,7 vs 2. | With deviations on, the player never split 8s against 9/10/A, a big EV loss. | Total-based Hit/Stand/Double deviations no longer override a basic-strategy Split. |
| 8 | High | **Index plays overrode late surrender.** 16 vs 10, 16 vs 9, 16 vs A and 15 vs 10 returned Hit/Stand, so surrender never happened. | With surrender + deviations on, the strategy was worse than plain basic strategy. | Hit/Stand deviations no longer override a basic-strategy Surrender. |
| 9 | Medium | **Soft 19 vs 6 index applied to the wrong game.** It was applied to H17 (where basic strategy already doubles) instead of S17. | The S17 deviation never fired. | Condition flipped to S17. |
| 10 | Low | **Soft 18 vs A index returned `Hit`.** Basic strategy already hits there, so the play did nothing; the correct S17 play is Stand at TC ≥ +1. | The deviation had no effect. | Returns Stand (S17). |
| 11 | Medium | **Basic-strategy table errors.** `hard.csv` (S17): 11 vs A was Double, should be Hit (that's why the "11 vs A +1" index exists). `soft.csv` (S17): A,7 vs 2 was Ds, should be Stand. `hard_h17.csv`: 17 vs A was S, should be Rs (surrender). | Small EV loss. | Cells corrected. |
| 11b | High | **Strategy CSVs loaded relative to the current working directory.** Run from any other directory, every table silently loaded as `{}` and the strategy defaulted to Hit everywhere. | Results were silently wrong. | Paths are resolved relative to the module. |
| 11c | Medium | **Free Bet + strategy editor dropped the free-hand tables.** The app always passes `custom_tables` from the editor, and that path never loaded `freehand_hard/soft`. | Free Bet sims in the app played free hands with the paid-hand strategy. | Default free-hand tables load when not supplied. |

### App (`app.py`)

| # | Severity | Bug | Fix |
|---|---|---|---|
| 12 | Medium | **Speed estimate never updated.** `measure_speed(_rules, _strategy_params)`: `st.cache_data` doesn't hash arguments whose names start with `_`, so the first estimate was reused for every configuration. | Renamed the parameters. |
| 13 | Medium | **Strategy editor lost edits.** The `data_editor` output was written back and fed in as the next input, so Streamlit treated it as new data and dropped in-progress edits. | Stable base DataFrame plus a versioned widget key. |
| 14 | Medium | **Uploaded strategy re-applied on every rerun.** The file uploader keeps its file, so any edit made after an upload was overwritten. | Each upload is applied once (tracked by `file_id`). |
| 15 | Low | **Win rate used the requested hand count as the denominator.** It was wrong after stop-on-ruin and didn't account for split hands. | Uses wins / (wins + losses + pushes). |
| 16 | Low | **Batch "sessions" / "hands" inputs accepted 0.** That caused a division by zero and stats on an empty array. | `min_value=1`. |
| 17 | Low | **Deprecated `use_container_width`.** It was scheduled for removal, and `requirements.txt` was unpinned. | `width="stretch"`, `streamlit>=1.50`; removed duplicate imports. |

### Counting

| # | Severity | Bug | Fix |
|---|---|---|---|
| 18 | High | **True count was wrong for unbalanced counts (KO).** KO adds +4 per deck even in a neutral shoe, but the TC was the raw RC ÷ decks remaining. Measured: mean KO TC **+3.31** (Hi-Lo: 0.00); TC ≥ 2 on 52% of hands vs 15%. So the bettor over-bet most of every shoe. | Subtract the count's expected drift (imbalance × decks dealt) before the conversion. Mean KO TC is now −0.03 and TC ≥ 2 is 16%. Balanced counts are unchanged. |

## Verification

- `python3 -m unittest discover tests`: 55 tests, all OK.
- House edge over 3M hands each (6D, DAS, LS, flat bet), ±0.13% at 2σ: **S17 −0.383%**, **H17 −0.573%**, consistent with published values (≈ −0.36% / −0.56%).
- Streamlit `AppTest` smoke test: Single Session, Batch, and Free Bet runs complete with no exceptions; editor state stays stable across reruns.

## Known limitations (not changed)

- **No non-DAS pair table.** `pair.csv` assumes DAS; with DAS off, splits of 2s/3s/4s/6s are slightly wrong.
- **Hi-Lo indices for every count.** Index plays and the insurance index (+3) are Hi-Lo values but are applied to whatever count is selected; insurance is only ever taken with Hi-Lo.
- **Ruin edge case.** With stop-on-ruin, a bankroll between $0 and $1 (from 3:2 or surrender halves) can't place a bet; the loop keeps advancing without playing instead of declaring ruin.
- **Stale root-level copies.** `test_*.py` in the repo root are older script-style copies of `tests/`, and `debug_*.py` are scratch scripts; CI only runs `tests/`.
