---
name: inducement
aliases: [IDM, engineered liquidity, liquidity engineering]
category: liquidity
related: [liquidity-sweep-stop-hunt, relative-equal-highs-lows, judas-swing, power-of-three]
parameters: {}
detection: not-implemented
---

# Inducement / Liquidity Engineering

The deliberate creation (or exploitation) of obvious retail reference points so that
stops and breakout orders accumulate where the algorithm intends to trade. Two common
forms:

1. **Engineered pools** — price paints relative equal highs/lows, trendline touches, or
   clean range boundaries; retail orders stack there; the level later gets run.
2. **Inducement before the array** — a minor pullback/swing is left just in front of a
   real PD array (order block / OTE zone). Retail enters at the shallow level; their
   stops become the fuel that delivers price into the deeper institutional zone.

Sequence example (bearish): price first drops to take out sell stops below a short-term
low (trapping breakout shorts), then reverses up through the relative equal highs to
take buy stops — institutions sell into those triggered buys, and the real move down
begins. The fake move *creates* the counterparty for the real one.

## Detection Rules

- Inducement sweep: a sweep of a *minor* pool (sub-swing inside the current leg) that
  precedes the sweep of the *major* pool in the opposite direction within the same
  session — flag as the two-step liquidity-engineering pattern.
- Practical filter: a sweep that occurs immediately in front of a higher-timeframe PD
  array carries more weight than one in open space.
- Per the project's elements-of-a-trade-setup decision: the prior fake-out is **not
  required** for the base model — treat inducement as a confluence feature, not a gate.

## Sources

- [Liquidity in forex trading — innercircletrader.net](https://innercircletrader.net/tutorials/liquidity-in-forex-trading/)
- [Day 4: Liquidity — tradingstrategyguides.com](https://tradingstrategyguides.com/liquidity-ict-smc-trading-explained/)
- Project notes: `strategies/notes/ict-elements-of-a-trade-setup.md` (liquidity engineering steps 4-5)
