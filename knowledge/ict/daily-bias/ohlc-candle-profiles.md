---
name: ohlc-candle-profiles
aliases: [OHLC, OLHC, candle expectation]
category: daily-bias
related: [daily-bias, power-of-three, judas-swing, true-day-midnight-open]
parameters:
  reference_open: "midnight NY open (true day open) for the daily candle"
detection: not-implemented
---

# OHLC / OLHC Candle Profiles

The expected internal sequence of a daily (or weekly) candle given the bias:

- **Bearish day = O-H-L-C**: Open → manipulation **High** (Judas swing above the open,
  often in London or early NY) → expansion to the **Low** → Close near the low.
- **Bullish day = O-L-H-C**: Open → manipulation **Low** below the open → expansion to
  the **High** → Close near the high.

This is the candle-anatomy view of [power-of-three](power-of-three.md): the open starts
accumulation, the move against bias creates the manipulation extreme, and the expansion
to the opposite extreme is distribution. Practical consequence: with a bullish bias, the
best longs are **below the daily open**; with a bearish bias, the best shorts are
**above the daily open**.

## Detection Rules

- Reference open: 00:00 NY midnight open (see [true-day-midnight-open](../time-and-price/true-day-midnight-open.md)).
- Classify a historical day: bullish profile if `time(low) < time(high)` and close in
  upper third of range; bearish if `time(high) < time(low)` and close in lower third.
- Entry-side filter for models: `if bias == long: require entry_price < daily_open`
  (buying at a discount to the open); mirror for shorts.
- Violation signal: bullish bias but price never trades below the open and expands
  immediately — either a runaway trend day or wrong bias; treat as no-setup.

## Sources

- [ICT Power of 3 — innercircletrader.net](https://innercircletrader.net/tutorials/ict-power-of-3/)
- [Power of 3 phases — tradingfinder.com](https://tradingfinder.com/education/forex/ict-power-of-three/)
- Project glossary (CLAUDE.md): OHLC/OLHC candle expectation
