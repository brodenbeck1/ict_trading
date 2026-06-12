---
name: cycle-order-flow
aliases: [previous cycle high low, cycle levels, order flow reading]
category: time-theory
related: [ninety-minute-cycles, session-opens]
ict_refs: [liquidity-pools, liquidity-sweep-stop-hunt, break-of-structure]
source_coverage: partial-public
parameters:
  reference_levels: "high and low of the previous 90-minute cycle (optionally previous 2 cycles)"
detection: not-implemented
---

# Cycle Order Flow

How Kishane reads directional intent from the time cycles: **the previous cycle's
high and low are the order-flow gauge for the current cycle**. Each new 90-minute
cycle inherits two levels, and what price does at them tells you the state:

- **Take the prior cycle high and hold above** → buy-side delivery; bullish order
  flow continues.
- **Take the prior cycle high and reject** → that run was the manipulation; expect
  delivery toward the prior cycle low (a cycle-scale purge, same logic as the CRT
  purge / ICT sweep).
- **Stay inside the prior cycle's range** → consolidation cycle; expect the *next*
  boundary to resolve it (liquidity builds for the following cycle).

This converts the ICT sweep-vs-run question into a clocked routine: every 90 minutes
there is a fresh, unambiguous pair of levels and a fresh read. Stacked across cycles,
the sequence of takes/rejections maps the session's delivery the way swing structure
does — but with time-defined rather than pattern-defined units.

## Detection Rules

- At each cycle boundary: emit `{prev_high, prev_low}` as active levels.
- Events within the cycle: `swept_prev_high` (trade above), `accepted` (close of
  m-minute subunit beyond, e.g., 15m close) vs `rejected` (close back inside),
  mirror for low, `inside_cycle` (neither touched).
- Order-flow state machine across cycles: sequences like reject-high → sweep-low →
  accept-low = bearish flow; feed as a bias feature into entry models.
- Aligns 1:1 with the existing sweep/run detectors in the ICT library — reuse them
  parameterized on cycle windows.

## Sources

- [90-minute cycle order flow — eightify.app](https://eightify.app/summary/trading-strategies/mastering-90-minute-cycle-times-expert-tips-for-successful-trading)
- [Time cycles indicators — tradingview.com](https://www.tradingview.com/script/tyfmkJIX-itradesize-Time-Cycles-x-Zeussy/)
