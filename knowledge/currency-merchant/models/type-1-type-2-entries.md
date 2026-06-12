---
name: type-1-type-2-entries
aliases: [type 1 entry, type 2 entry, expanding market entries]
category: models
related: [pa-flow, rules-of-engagement, cycle-order-flow]
ict_refs: [displacement, entry-sequence, break-of-structure]
source_coverage: sparse-public   # named in the curriculum ("Entering in expanding markets — Type 1 and 2"); definitions paywalled
parameters: {}
detection: not-implemented
---

# Type 1 & Type 2 Entries (Expanding Markets)

The CM Academy module for **entering a market that is already expanding** — the
continuation problem (the orderblock Rules of Engagement handle the reversal/retrace
problem). The curriculum names two entry types but their precise definitions are in
the paywalled material; the consistent community reading:

- **Type 1** — entry on the first orderly retracement *within* the expansion: the
  pullback into the leg's own inefficiency (gap/VI/OB candidate formed by the
  expansion), in the direction of the flow. The earlier, with-momentum entry.
- **Type 2** — entry on the deeper, second-stage opportunity: the retest after a
  continuation structure break, or the next cycle's return to the prior cycle's
  levels. The later, confirmation-heavy entry.

**Treat the above as provisional** — verify and replace with Kishane's own
definitions via `/strategy-from-transcript` when processing his entry videos. What
is firm: both types are conditioned on the PA flow being in the *expansion* state,
and they pair with the time cycles (entries near cycle boundaries in the flow
direction).

## Detection Rules (provisional)

- Precondition: PA-flow classifier reports `expansion` and cycle order flow agrees
  with the leg direction.
- Type 1 trigger: first retrace into an inefficiency created by the active expansion
  leg (reuse ICT FVG/OB detectors scoped to the leg).
- Type 2 trigger: continuation BOS after the retrace, enter on the retest of the
  break level / the gap left by the breaking candle.
- Backtest both as separate exit-tagged variants to compare fill rate vs. quality.

## Sources

- [CM Academy outline ("Entering in expanding markets Type 1 and 2") — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
