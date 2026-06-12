---
name: key-level-coupling
aliases: [key levels, HTF coupling, level hierarchy]
category: protocols
related: [quality-protocols, purge, crt-range]
ict_refs: [rejection-block, order-block, fair-value-gap, breaker-block, pd-array-matrix]
parameters:
  hierarchy: "rejection block > order block > fair value gap > breaker (highest to lowest quality per source)"
  coupling_tf_rule: "key levels come from one timeframe ABOVE the CRT timeframe (4H CRT -> daily key levels)"
detection: not-implemented
---

# Key-Level Coupling

A CRT purge is highest-grade when the purged extreme lands **into a higher-timeframe
key level** — the range's stop raid doubles as the HTF array's mitigation. The
methodology imports the ICT PD-array vocabulary wholesale and ranks it:

1. **Rejection block** (highest quality)
2. **Order block**
3. **Fair value gap**
4. **Breaker** (lowest of the four)

Coupling rule: levels are drawn from **one timeframe above the CRT timeframe** —
a 4H CRT couples with daily key levels; a daily CRT with weekly levels. The purge
into the level provides the *reason* the range resolves there; the CRT provides the
*structure* to trade it with (defined range, defined targets).

All four level types are defined in the ICT library
([pd-arrays/](../../ict/pd-arrays/)) — this file only adds the coupling and
ranking logic.

## Detection Rules

- For each CRT, query the ICT-library PD-array registry one timeframe up for
  unmitigated zones overlapping a band around each range extreme
  (band: e.g., ±0.25 × range height).
- `coupled = purge wick intersects a registered HTF zone`; record zone type and apply
  the hierarchy as a quality weight.
- Note for backtests: the ranking (RB > OB > FVG > breaker) is another testable
  claim — log zone type per trade and measure.

## Sources

- [Mastering CRT (key levels hierarchy) — scribd.com](https://www.scribd.com/document/898327293/Crt)
- [CRT key levels — grandalgo.com](https://grandalgo.com/blog/candle-range-theory-crt-explained)
