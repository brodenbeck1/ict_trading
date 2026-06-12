---
name: one-shot-one-kill
aliases: [OSOK]
category: models
related: [weekly-profiles, ipda-lookbacks, optimal-trade-entry, killzones, daily-bias]
parameters:
  setup_days: [Monday, Tuesday, Wednesday]
  dealing_range: "20-day/20-week IPDA range for context"
  entry: "OTE (62-79%) at a HTF PD array during London or NY killzone, 15m execution"
  weekly_objective: "one trade per week; FX original targets 50-75 pips — index analog: one weekly-range leg"
detection: not-implemented
---

# One Shot One Kill (OSOK)

A **weekly cadence model and philosophy**: one high-confluence setup per week, framed
on the weekly range, executed once, managed to a fixed objective. The discipline layer
matters as much as the entry: no revenge trades, no second shots.

Framework:
1. Mark the IPDA dealing range (20 days / 20 weeks): highs, lows, equilibrium.
2. Establish the weekly bias and expected [weekly profile](../daily-bias/weekly-profiles.md).
3. Expect the **anchor extreme to form Mon–Wed** (e.g., Tuesday-London low in a
   bullish week) at a HTF PD array.
4. Enter on the **OTE retracement** of the displacement off that anchor, during a
   London/NY killzone on ~15m.
5. Original FX spec: take 80% at +50 pips, runner to 75. Index translation: scale at
   the first weekly-range objective (e.g., weekly EQ or opposing session pool), runner
   toward the weekly draw.

OSOK is the weekly-scale wrapper around the same primitives — it mostly *constrains
frequency and context* rather than introducing new mechanics.

## Detection Rules

- Calendar gate: setup search active Mon-Wed only; one position per week.
- Context gates: price at/beyond a 20-day range quartile + HTF array; weekly bias set.
- Entry: OTE fill of the post-anchor displacement leg within a killzone.
- Backtest metric: weekly hit-rate and average capture vs. the weekly range height
  (did the model capture the Tue-low → weekly-high style leg?).

## Sources

- [ICT one shot one kill — innercircletrader.net](https://innercircletrader.net/tutorials/ict-one-shot-one-kill/)
- [OSOK guide — tradingfinder.com](https://tradingfinder.com/education/forex/ict-one-shot-one-kill/)
- [OSOK weekly plan — fxmarkethours.com](https://fxmarkethours.com/ict-one-shot-one-kill-trading-model/)
