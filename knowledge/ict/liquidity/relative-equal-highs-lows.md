---
name: relative-equal-highs-lows
aliases: [REH, REL, equal highs, equal lows, EQH, EQL]
category: liquidity
related: [buyside-sellside-liquidity, liquidity-sweep-stop-hunt, inducement]
parameters:
  tolerance: "max distance between touches to count as 'equal'; project decision: dynamic, starts at 20 NQ points, configurable per instrument"
  min_touches: 2
  min_separation_bars: "touches must be distinct swings, not the same swing"
detection: implemented
---

# Relative Equal Highs / Lows

Two or more swing highs (or lows) at approximately the same price. Retail reads these
as double-top resistance / double-bottom support; ICT reads them as **engineered
liquidity** — a clean shelf of stops that the algorithm is incentivized to run. Equal
lows advertise sell stops beneath; equal highs advertise buy stops above.

The cleaner and more visible the level (more touches, flatter line, higher timeframe),
the stronger the draw — and the more likely a sweep through it is a terminus
(reversal point) rather than a breakout.

## Detection Rules

- Collect confirmed swing highs within a rolling window (e.g., one session or one
  dealing range).
- Two swings `s1, s2` form relative equal highs if
  `abs(s1.high - s2.high) <= tolerance` and they are separated by at least one
  opposing swing.
- Tolerance scales with volatility: e.g., `tolerance = k * ATR(14)` on the working
  timeframe, floor/ceiling per instrument (project default: 20 NQ pts starting point).
- The pool level = `max(touch highs)` (for equal highs) — stops sit above the highest
  touch; pool is consumed only when that price is violated.
- **Every touch must still be resting.** A cluster is only valid engineered liquidity
  if no member has been traded through since *its own* formation. If price ran beyond
  any touch — even before a later equal swing reprinted the level — the shelf has
  already been swept and the cluster is dead. A fresh equal swing at a previously-run
  price is not a revival of that liquidity. (See `first_breach` in the
  liquidity-sweep-stop-hunt concept for the per-pool "still live?" rule.)

## Sources

- [Liquidity in forex (equal highs/lows) — innercircletrader.net](https://innercircletrader.net/tutorials/liquidity-in-forex-trading/)
- [BSL/SSL & equal highs — tradingfinder.com](https://tradingfinder.com/education/forex/ict-bsl-ssl/)
- Project decision log: `strategies/notes/ict-elements-of-a-trade-setup.md` (tolerance)
