---
name: gap-vi-entry
aliases: [enter at the gap, VI entry, gap refinement]
category: orderblocks
related: [rules-of-engagement, voids-in-delivery]
ict_refs: [volume-imbalance, fair-value-gap, order-block, consequent-encroachment]
source_coverage: partial-public
parameters:
  rule: "if the orderblock candidate's range contains a gap or volume imbalance, place the entry at the gap instead of the block edge"
detection: not-implemented
---

# Gap / VI Entry Refinement

The publicly quoted CM entry confluence: **"if the range of the orderblock candidate
has a gap or VI, enter at the gap."** The inefficiency *inside* the block marks where
the algorithm actually transacted one-sidedly — so the limit order goes at the gap's
level rather than the block's outer edge, improving both fill price and stop
distance.

This is the CM counterpart of the ICT practice of refining an OB entry to an embedded
FVG/volume-imbalance or to the block's mean threshold — with Kishane making the
override explicit and mechanical: gap present → gap *is* the entry.

## Detection Rules

- For each qualified orderblock candidate (per
  [rules-of-engagement](rules-of-engagement.md)): scan the candle(s) composing the
  block and its immediate formation leg for FVG / volume-imbalance zones intersecting
  the block's range (reuse ICT-library detectors).
- If found: `entry_price = gap zone edge nearest current price` (config alt: gap CE);
  else `entry_price = block edge / mean threshold` per the base rules.
- Stop remains beyond the block (or the raided extreme); the refinement shrinks risk
  — log both candidate and refined entry to measure the improvement empirically.

## Sources

- [CM Academy quoted entry confluence — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
