---
name: quality-protocols
aliases: [protocols, CRT grading, probability stacking]
category: protocols
related: [timing-protocol, key-level-coupling, inside-bars-accumulation, crt-range]
ict_refs: [entry-sequence]
parameters:
  claimed_boost_per_protocol: "+11% probability per added protocol (source's claim — treat as hypothesis to test, not fact)"
detection: not-implemented
---

# Quality Protocols

CRT's selection system: a raw range-purge happens constantly; the edge (per the
methodology) comes from only trading CRTs that satisfy stacked **protocols**. Each
satisfied protocol upgrades the setup; the source material claims roughly +11%
probability per protocol added — a marketing-flavored number this project should
treat as a *testable hypothesis*, not an input.

The protocol stack:

1. **Timing** — the range candle opens at a key time, and/or the purge occurs at a
   key time ([timing-protocol](timing-protocol.md)). "Time > Price."
2. **Inside bars** — accumulation inside the range before the purge
   ([inside-bars-accumulation](../ranges/inside-bars-accumulation.md)).
3. **Key-level coupling** — the purged extreme sits at a higher-timeframe key level
   ([key-level-coupling](key-level-coupling.md)).
4. **LTF confirmation** — CISD/MSS on the timeframe below after the purge
   ([entry-triggers](../entries/entry-triggers.md)).
5. **HTF narrative** — the implied delivery direction agrees with the higher range's
   position (e.g., purge low while in the daily range's discount).

This is CRT's version of the ICT rule of exclusion, expressed as a score rather than
a hard gate — models can implement it either way (min-score gate or all-required).

## Detection Rules

- Score each CRT: `score = sum(protocol_flags)`; log per-protocol booleans in the
  trade record so the backtest can measure each protocol's marginal lift directly.
- Config: `min_score` gate and/or required-protocol mask.
- Research deliverable: protocol ablation table (win rate / PF by protocol subset) —
  empirically replaces the +11% folklore.

## Sources

- [Mastering CRT (protocols) — scribd.com](https://www.scribd.com/document/898327293/Crt)
- [Choosing the best CRT — rattibha.com](https://en.rattibha.com/thread/1790141530461622525)
- [CRT study guide — studylib.net](https://studylib.net/doc/27924459/candle-range-theory)
