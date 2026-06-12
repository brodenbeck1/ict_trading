---
name: pd-array-matrix
aliases: [PD arrays, premium discount arrays, PDA matrix]
category: pd-arrays
related: [premium-discount, fair-value-gap, order-block, breaker-block, mitigation-block, rejection-block, liquidity-void, dealing-range]
parameters: {}
detection: not-implemented
---

# PD Array Matrix

**PD array** = Premium/Discount array: any institutional reference level price may
react to. The "matrix" is ICT's ordered checklist of these arrays within a dealing
range, scanned from equilibrium outward:

**Premium arrays (above EQ — sell-side interest)**: old highs, rejection blocks,
bearish order blocks, fair value gaps, liquidity voids, bearish breakers/mitigation
blocks.

**Discount arrays (below EQ — buy-side interest)**: mirror image — old lows, bullish
order blocks, FVGs, voids, bullish breakers/mitigation blocks.

Usage logic:
- With a **bearish** bias, look for entries at *premium* arrays (sell high);
- With a **bullish** bias, at *discount* arrays (buy low);
- Targets are the opposing arrays on the way to the draw on liquidity.
- When multiple arrays overlap (e.g., FVG inside a breaker = [Unicorn](../models/unicorn.md)),
  the zone is stronger.

## Detection Rules

- Maintain a per-range registry of all detected arrays: {type, zone_high, zone_low,
  timeframe, created_at, mitigated_at, side (premium/discount)}.
- Grade arrays by: timeframe (higher = stronger), freshness (unmitigated > tested),
  confluence (overlaps), and position in the range (deeper premium/discount = better
  price).
- A model's entry question becomes a registry query: "nearest unmitigated discount
  array below current price within the active range, formed by displacement."

## Sources

- [Understanding PD arrays — fxopen.com](https://fxopen.com/blog/en/what-is-a-pd-array-in-ict-and-how-can-you-use-it-in-trading/)
- [ICT PD array matrix — writofinance.com](https://www.writofinance.com/ict-pd-array-matrix-in-forex/)
