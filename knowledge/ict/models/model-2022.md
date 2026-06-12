---
name: model-2022
aliases: [2022 model, 2022 mentorship model]
category: models
related: [entry-sequence, daily-bias, liquidity-sweep-stop-hunt, market-structure-shift, fair-value-gap, killzones]
parameters:
  entry_timeframe: 3m            # FVGSweepModel entry/MSS timeframe (spec range 1–5m)
  min_rr: 3                      # target floor; falls back to fixed 3R when nearest pool is closer
  primary_array: fair-value-gap
  pool_set: [PDH/PDL, midnight-opening-range, session-swings, relative-equal-highs-lows]
  killzones: [london, ny_am]     # 02:00–05:00 NY and 07:00–10:00 NY
  bias: "daily — order flow + draw + premium/discount must align"
detection: implemented           # FVGSweepModel (src/ict/models/ict/fvg_sweep.py)
---

# The 2022 Model

The intraday model from ICT's free 2022 YouTube mentorship — the purest expression of
the [canonical entry sequence](../entries/entry-sequence.md), and effectively the
formal version of this project's elements-of-a-trade-setup note:

1. **Daily bias** from the daily chart (order flow + imbalance + draw).
2. **Mark the session liquidity** — previous day H/L, midnight/opening range, session
   extremes.
3. **Wait for the sweep** — a raid of the pool *against* bias (the Judas move),
   inside London or NY killzone.
4. **MSS with displacement** on 1m/3m/5m in the bias direction; the displacement must
   leave an FVG.
5. **Entry**: limit in that FVG on the retrace. **Stop**: beyond the swept extreme.
   **Target**: opposing liquidity, minimum **1:3 R:R**.

Distinctives vs. other models: FVG is the primary (near-exclusive) entry array; the
model is time-gated but not minute-precise (unlike Silver Bullet); one good setup per
session.

## Detection Rules

- Direct instantiation of the entry-sequence state machine with:
  `pool_set = {PDH/PDL, session H/L, midnight opening range}`,
  `array_filter = FVG only`, `rr_gate = 3`,
  `killzones = {london, ny_am}` (config).
- All project conventions (3-bar swings, stop at swept extreme, no-chase rule)
  apply unchanged.

## Sources

- [Complete ICT 2022 strategy — innercircletrader.net](https://innercircletrader.net/tutorials/complete-ict-trading-strategy-2022/)
- [2022 mentorship model — tradingfinder.com](https://tradingfinder.com/education/forex/ict-mentorship-2022-model/)
- [2022 mentorship guide — crypoptionhub.com](https://crypoptionhub.com/ict-mentorship-2022/)
