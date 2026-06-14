# Model 2022 — Daily Bias Signal Study

**Model**: model-2022  
**Concept**: daily-bias  
**Instrument**: NQ  
**Analysis date**: 2026-06-13  
**Dataset**: NQ continuous contract, 2010–2025 (~4,788 trading days)  
**Scripts**: `backtests/daily_bias_grid_search.py`, `backtests/daily_bias_accuracy.py`, `backtests/fvg_sweep_backtest.py`  
**Raw results**: `results/daily_bias_grid_20260613_121349.csv`, `results/daily_bias_accuracy.csv`  
**Configs**: `configs/model_2022/bias_4h_soft.yaml`, `configs/model_2022/bias_4h_hard.yaml`

---

## What Was Tested

### Part 1: Signal combination grid search

Walk-forward test across 60 parameter sets × 12 gate combinations (720 total). For each day, bias was computed from data strictly before that day's open, then checked against actual close vs open direction.

**Parameter grid:**

| Parameter | Values tested |
|---|---|
| `lookback` (order-flow window, daily bars) | 3, 5, 10, 20, 30 |
| `dealing_range_days` (DOL + P/D window) | 10, 20, 40, 60 |
| `swing_lookback` (swing detection radius) | 2, 3, 5 |

**Gate combinations (12):**

| Gate | Signals required | 4H behaviour |
|---|---|---|
| `order_flow_only` | Daily order flow alone | — |
| `draw_only` | DOL alone | — |
| `four_h_only` | 4H structure alone | — |
| `of_draw` | Order flow + DOL | — |
| `of_draw_4h_soft` | OF + DOL + 4H | neutral 4H abstains *(current impl)* |
| `of_draw_4h_hard` | OF + DOL + 4H | neutral 4H vetoes |
| `of_4h_soft` | OF + 4H | neutral 4H abstains |
| `draw_4h_soft` | DOL + 4H | neutral 4H abstains |
| `of_pdm` | OF + prior-day midpoint | — |
| `draw_pdm` | DOL + prior-day midpoint | — |
| `of_draw_pdm` | OF + DOL + PDM | — |
| `of_draw_4h_soft_pdm` | OF + DOL + 4H + PDM | neutral 4H abstains |

**Metrics:** `bull_acc`, `bear_acc`, `overall_acc`, `neutral_rate`, `coverage_score` (`overall_acc × signal_rate`)

### Part 2: Full model backtest (soft vs hard 4H gate)

Ran `bias_4h_soft` and `bias_4h_hard` configs against the full FVG sweep model, NQ, 2022-01-01 → 2025-11-17.

---

## Results — Best Per Gate (by coverage score)

| Gate | lb | deal | sw | Signals | Neutral% | Bull% | Bear% | Acc% | Coverage |
|---|---|---|---|---|---|---|---|---|---|
| `draw_only` | 30 | 20 | 2 | 4,730 | 0.5% | 55.1% | 44.3% | 49.6% | 0.4936 |
| `order_flow_only` | 30 | 60 | 3 | 3,972 | 15.9% | 55.4% | 45.1% | **52.9%** | 0.4446 |
| `of_4h_soft` | 30 | 60 | 3 | 3,845 | 18.6% | 55.3% | 44.9% | 52.8% | 0.4302 |
| `four_h_only` | 3 | 60 | 3 | 3,914 | 17.1% | 55.5% | 44.7% | 51.5% | 0.4264 |
| `draw_4h_soft` | 30 | 60 | 2 | 3,021 | 36.0% | 54.7% | 44.0% | 51.6% | 0.3301 |
| `of_pdm` | 3 | 10 | 5 | 2,712 | 43.2% | 56.6% | 45.2% | 52.3% | 0.2973 |
| `draw_pdm` | 30 | 60 | 5 | 2,272 | 51.9% | 56.0% | 46.2% | 51.4% | 0.2475 |
| `of_draw` | 30 | 60 | 2 | 2,105 | 55.4% | 55.3% | 44.4% | 52.5% | 0.2340 |
| `of_draw_4h_soft` *(current)* | 30 | 60 | 2 | 2,041 | 56.8% | 55.2% | 45.1% | 52.7% | 0.2278 |
| `of_draw_4h_hard` | 30 | 60 | 2 | 1,642 | 65.2% | 55.4% | **47.4%** | **54.2%** | 0.1884 |
| `of_draw_pdm` | 10 | 60 | 2 | 1,249 | 73.6% | 56.2% | 43.8% | 52.0% | 0.1376 |
| `of_draw_4h_soft_pdm` | 30 | 60 | 2 | 1,167 | 75.3% | 55.7% | 45.5% | 53.5% | 0.1321 |

---

## Full Backtest — Soft vs Hard 4H Gate

*NQ, 2022-01-01 → 2025-11-17 (1,417 trading days). Params: lb=30, deal=60, sw=2.*

| Metric | bias_4h_soft | bias_4h_hard | Delta |
|---|---|---|---|
| Signals fired | 85 | 72 | −13 (−15%) |
| No-fill | 20 (24%) | 15 (21%) | −5 |
| Filled trades | 65 | 57 | −8 |
| Win rate | 15.4% (10W/53L) | 15.8% (9W/46L) | +0.4 pp |
| Avg win | 72.4 pts | 73.8 pts | +1.4 pts |
| Avg loss | −18.7 pts | −18.9 pts | −0.2 pts |
| Avg R:R (setup) | 3.64 | 3.64 | = |
| Profit factor | 0.73 | **0.77** | +0.04 |
| Total P&L | −$4,875 (−243.8 pts) | **−$3,610 (−180.5 pts)** | +$1,265 |
| Max drawdown | −$7,375 | **−$6,405** | +$970 |
| Sharpe ratio | −1.74 | **−1.43** | +0.31 |

---

## Kill Zone Breakdown (bias_4h_soft, 65 trades)

### By session

| Kill Zone | Trades | Win% | P&L pts | Avg win | Avg loss |
|---|---|---|---|---|---|
| London (02:00–05:00 UTC) | **0** | — | — | — | — |
| NY AM (07:00–10:00 UTC) | 11 | 9.1% | −131.5 | 60.0 | −19.1 |
| NY PM (13:30–16:00 UTC) | 41 | 14.6% | −260.5 | 68.0 | −19.1 |
| Outside defined KZ | 13 | **30.8%** | **+148.2** | 69.8 | −14.6 |

### By session × direction

| Kill Zone | Dir | Trades | Win% | P&L pts |
|---|---|---|---|---|
| NY AM | long | 7 | **0.0%** | −131.5 |
| NY AM | short | 4 | 25.0% | 0.0 |
| NY PM | long | 26 | 19.2% | −46.5 |
| NY PM | short | 15 | 6.7% | −214.0 |
| Outside KZ | long | 8 | 25.0% | +45.8 |
| Outside KZ | short | 5 | 40.0% | +102.5 |

### Outside-KZ entry times (the profitable "gap" window)

Entries classified as "Outside KZ" cluster in two windows:
- **10:00–13:30 UTC** (between London close and NY AM open): 2022-03-07 12:52, 2022-05-04 12:28, 2023-07-26 12:38, 2024-04-16 12:28, 2024-08-14 10:46, 2025-02-13 12:12
- **After 16:00 UTC** (after NY PM close): 2022-11-11 16:14, 2023-03-30 18:38, 2023-08-25 18:16, 2025-05-28 19:14, 2025-06-09 20:00, 2025-11-17 16:06

The 10:00–13:30 UTC window (pre-market / "AM session" in ICT terms) contains 3 of the 4 biggest winning trades:
- 2024-08-14 at 10:46 UTC: **+89 pts**
- 2025-02-13 at 12:12 UTC: **+107.5 pts**
- 2022-05-04 at 12:28 UTC: **+60 pts**

---

## Key Findings

### 1. Order flow is the dominant signal

`order_flow_only` (lb=30) achieves 52.9% accuracy on 84% of days — nearly as accurate as any multi-signal gate. Every gate that adds DOL without 4H barely moves the needle on accuracy while cutting signal days by ~50%. Lookback of 30 bars (≈6 weeks) consistently outperforms shorter windows.

### 2. Draw-on-liquidity alone is below coin flip

`draw_only` signals 99.5% of days at 49.6% accuracy — worse than guessing. DOL is valuable as a confirmation gate, not a standalone.

### 3. Hard 4H gate is the highest-accuracy combination

`of_draw_4h_hard` achieves 54.2% overall and 47.4% bearish accuracy — the best bearish result across all 720 combinations. Forces 4H to actively agree, filtering out directionless days. Cost: 65% neutral rate (trading ~1 in 3 days).

### 4. Bearish accuracy is structurally weak across the board

No gate breaks 47.5% bearish accuracy. This reflects the 2010–2025 secular bull trend in NQ. The 2022 bear market is the cleanest test for bearish bias performance.

### 5. Prior-day midpoint adds noise, not signal

PDM gates reduce frequency without improving accuracy. Should remain a reference-only signal.

### 6. London session produces zero trades

Zero entries in the 02:00–05:00 UTC killzone across all bias-gated configurations. Either the FVG/sweep/MSS setup doesn't form within that 3-hour window, or the bias filter eliminates everything before London develops a clean structure.

### 7. NY AM longs are 0-for-7

Every long taken in the 07:00–10:00 UTC window lost. NY AM shorts (25%, 1/4) are marginally better. Taking longs in the pre-RTH session is consistently destructive.

### 8. The 10:00–13:30 UTC window is untapped

Three of the four biggest wins came in the pre-market window that sits between the London and NY AM killzones. This window is not defined in the current killzone config. Adding it as a killzone or extending London to 10:00 UTC is worth testing.

### 9. The deeper problem is execution, not bias

Both configs are net losers. The hard gate is better across every metric but neither is profitable. Breakeven win rate at 3.64 avg R:R is 21.6%; both configs run at 15–16%. The bias filter is doing its job (52–54% directional accuracy). The losses are coming from the execution layer:
- 24% of bias signals don't fill the FVG entry
- 85% of filled trades hit stop before reaching 3R
- 20pt max stop is too tight for 2023–2025 NQ volatility (200–400 pts/day ranges)

---

## Recommendations

| Action | Priority | Why |
|---|---|---|
| Switch to `of_draw_4h_hard` | High | +1.5% accuracy, best bearish, consistent improvement across all metrics |
| Test stop_mode: atr | High | 20pt wick stop too tight for current NQ volatility |
| Add 10:00–13:30 UTC killzone | Medium | 3 of 4 biggest wins came from this window |
| Disable NY AM longs | Medium | 0-for-7, −131.5 pts; remove or flag as excluded |
| Re-run bearish accuracy on 2022 only | Low | Validate whether bearish bias works in an actual bear market |
| Test wider max_stop_pts (30–40) | Low | May improve fill rate and let winners breathe |

---

## Open Questions

- Does the 10:00–13:30 UTC window have an ICT name / concept that should gate entries there?
- Would SMT divergence across ES/NQ/YM at session open sharpen the daily bias accuracy?
- Does NY AM long weakness persist across ES and YM, or is it NQ-specific?
- At what stop size does the model become profitable? (max_stop_pts sensitivity test)
