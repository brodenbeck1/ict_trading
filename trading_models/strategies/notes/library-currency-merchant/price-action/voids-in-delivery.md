---
name: voids-in-delivery
aliases: [voids, voids in price delivery]
category: price-action
related: [pa-flow, imbalances-to-liquidity, gap-vi-entry]
ict_refs: [liquidity-void, fair-value-gap, volume-imbalance]
source_coverage: sparse-public
parameters: {}
detection: not-implemented
---

# Voids in Price Delivery

A named CM Academy module: the inefficiencies left when price is delivered one-sidedly
— the gaps, volume imbalances, and multi-candle voids that expansion legs leave
behind. Kishane's treatment (per the curriculum outline and his entry rules) uses
voids in two roles:

1. **Magnets** — open voids are unfinished delivery; price returns to them
   (identical to the ICT liquidity-void / FVG magnet logic).
2. **Entry refinements** — his Rules of Engagement state that when an orderblock
   candidate's range contains **a gap or volume imbalance (VI), the entry goes at the
   gap** rather than the block edge (see [gap-vi-entry](../orderblocks/gap-vi-entry.md))
   — the void inside the zone is the precise level the algorithm defends.

Definitions of the underlying objects live in the ICT library
([liquidity-void](../../library/liquidity/liquidity-void.md),
[fair-value-gap](../../library/pd-arrays/fair-value-gap.md),
[volume-imbalance](../../library/pd-arrays/volume-imbalance.md)) — this file records
the CM usage pattern.

## Detection Rules

- Reuse ICT-library FVG/void/VI detectors unchanged.
- CM-specific feature: for each orderblock candidate, `contains_void` flag + the
  void's price band (drives the entry-price override in the rules of engagement).
- Track void fill state per 90-minute cycle: voids created in one cycle and filled
  in the next are the expected rhythm; voids that survive multiple cycles gain
  magnet weight.

## Sources

- [CM Academy outline ("Voids in price delivery") — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
