---
name: model-2022
aliases: [2022 model, 2022 mentorship model]
category: models
related: [entry-sequence, daily-bias, liquidity-sweep-stop-hunt, market-structure-shift, fair-value-gap, killzones]
parameters:
  entry_timeframe: 2m            # FVGSweepModel entry/MSS timeframe (spec range 1–5m)
  min_rr: 3                      # target floor; falls back to fixed 3R when nearest pool is closer
  max_stop_pts: 20               # stop cap: if swept wick is further than 20 pts from entry, stop is clamped to entry ± 20 pts
  primary_array: fair-value-gap
  pool_set: [PDH/PDL, Chicago-prior (09:15–12:00 NY prior day), ONS (05:00–09:15 NY), opening-range (09:30–10:00 NY), Chicago-same-day, session-swings, relative-equal-highs-lows]
  killzones: [london, ny_am, ny_pm]  # 02:00–05:00 NY, 07:00–10:00 NY, 13:30–16:00 NY
  bias: "daily — order flow + draw must align (gate); premium/discount is a logged entry-zone check, not a gate"
detection: implemented           # Model2022 (src/ict/models/ict/model_2022.py)
---

# The 2022 Model

The intraday model from ICT's free 2022 YouTube mentorship — the purest expression of
the [canonical entry sequence](../entries/entry-sequence.md), and effectively the
formal version of this project's elements-of-a-trade-setup note:

1. **Daily bias** from the daily chart — order flow + draw must agree (the gate).
   Premium/discount is computed and logged as an entry-zone check but is *not* a gate
   (a trending day sits in discount/premium by definition).
2. **Mark the session liquidity** — previous day H/L, the prior day's **09:15–12:00 NY
   Chicago range** (next-day pool), the **05:00–09:15 NY overnight session (ONS)** range,
   the **09:30–10:00 NY opening range**, relative-equal highs/lows. The same-day Chicago
   range becomes a pool at noon and is sweepable in the PM killzone.
3. **Wait for the sweep** — a raid of the pool *against* bias (the Judas move),
   inside London or NY killzone. The pool must still be **live**: the raid has to be
   the level's *first* breach since it formed (already-run pools are dead), and a
   relative-equal cluster is only valid if *every* member is still resting.
4. **MSS with displacement** on 1m/2m/5m in the bias direction; the displacement must
   leave an FVG.
5. **Entry**: limit in that FVG on the retrace. **Stop**: beyond the swept extreme.
   **Target**: opposing liquidity, minimum **1:3 R:R**.

Distinctives vs. other models: FVG is the primary (near-exclusive) entry array; the
model is time-gated but not minute-precise (unlike Silver Bullet); one good setup per
session.

## Detection Rules

- Direct instantiation of the entry-sequence state machine with:
  `pool_set = {PDH/PDL, Chicago-prior (next-day), ONS 05:00–09:15 NY, 09:30–10:00 NY opening range, Chicago-same-day (noon), session H/L, REH/REL}`,
  `array_filter = FVG only`, `rr_gate = 3`,
  `killzones = {london, ny_am}` (config).
- **Bias gate** is order-flow + draw only; premium/discount is logged, not gated.
- **Liquidity validity** (see liquidity-sweep-stop-hunt, relative-equal-highs-lows):
  a sweep must be the pool's first breach since formation, landing in a killzone;
  the OR cannot be swept before its `range_end`; REH/REL clusters with any already-run
  member are discarded.
- **Stop** sits beyond the *swept extreme* (the wick that raided the pool), never at
  the pool level itself — that price has already traded through. Capped at 20 pts from
  entry: if the swept wick is further away, the stop is clamped to `entry ± 20 pts`.
- **Target pools are validity-checked**: any opposing pool already run before entry is
  filtered out — dead liquidity is not a draw. Only live pools are passed to
  `find_liquidity_target`.
- Remaining project conventions (3-bar swings, no-chase rule) apply unchanged.

## Sources

- [Complete ICT 2022 strategy — innercircletrader.net](https://innercircletrader.net/tutorials/complete-ict-trading-strategy-2022/)
- [2022 mentorship model — tradingfinder.com](https://tradingfinder.com/education/forex/ict-mentorship-2022-model/)
- [2022 mentorship guide — crypoptionhub.com](https://crypoptionhub.com/ict-mentorship-2022/)
