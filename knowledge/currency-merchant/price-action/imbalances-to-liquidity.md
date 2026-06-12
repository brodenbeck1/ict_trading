---
name: imbalances-to-liquidity
aliases: [imbalance to liquidity, I2L]
category: price-action
related: [pa-flow, voids-in-delivery]
ict_refs: [internal-external-range-liquidity, draw-on-liquidity, fair-value-gap]
source_coverage: sparse-public
parameters: {}
detection: not-implemented
---

# Imbalances to Liquidity

A CM Academy module name that encodes the delivery alternation rule: **price moves
from imbalance to liquidity and from liquidity to imbalance**. At any moment the
current objective is one of the two:

- Just rebalanced an imbalance (filled a void/FVG)? → the next draw is **liquidity**
  (a high/low, equal extremes, a prior cycle's extreme).
- Just took liquidity (swept a pool)? → the next draw is **imbalance** (the nearest
  unfilled void/gap in the new direction).

This is the same engine as the ICT library's
[internal-external-range-liquidity](../../ict/liquidity/internal-external-range-liquidity.md)
alternation (IRL ↔ ERL), expressed without the dealing-range wrapper — and in
Kishane's system it runs on the **time-cycle grid**: each 90-minute cycle's delivery
is read as one hop of the imbalance↔liquidity sequence, with the prior cycle's
extremes as the liquidity side.

## Detection Rules

- Maintain the two registries (liquidity pools; unfilled imbalances) from the ICT
  library detectors.
- State per instrument: `last_taken ∈ {liquidity, imbalance}` → next expected
  objective type; resolve the nearest qualifying instance in the bias direction.
- Cycle-aligned variant: evaluate the hop at 90-minute boundaries; a cycle that
  completes both (sweeps liquidity AND rebalances) is an expansion cycle marker.

## Sources

- [CM Academy outline ("Imbalances to Liquidity") — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
