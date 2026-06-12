---
name: dealing-range
aliases: [range, trading range]
category: market-structure
related: [premium-discount, internal-external-range-liquidity, ipda-lookbacks, swing-points]
parameters:
  anchor_rule: "swing high and swing low that both swept liquidity (or IPDA 20-day extremes for HTF)"
detection: not-implemented
---

# Dealing Range

The price zone between a meaningful swing high and swing low that currently "contains"
delivery. The dealing range is the measuring stick for nearly everything else:

- **Equilibrium** = 50% of the range; above = premium, below = discount
  (see [premium-discount](../pd-arrays/premium-discount.md)).
- Range extremes hold **external range liquidity**; imbalances inside hold **internal
  range liquidity**.
- PD arrays are only graded *within* the active dealing range.

The cleanest anchors are swings that **swept liquidity** at both ends — a high that ran
buy stops and a low that ran sell stops define a range the algorithm is actually
dealing within. Ranges are fractal: an intraday 5m dealing range nests inside the daily
range, which nests inside the IPDA 20-day range; use the timeframe relevant to the
model's holding period.

## Detection Rules

- HTF default: 20-trading-day high/low (IPDA) or the most recent confirmed
  intermediate-term swing high/low pair.
- Intraday default: the high/low of the leg between the last two opposing liquidity
  sweeps, or the prior session's range.
- Recompute when an extreme is *accepted* (close beyond + continuation) — that breaks
  the range and starts a new one; a mere sweep does not.
- Derived outputs: `eq = (high + low)/2`, quartiles (0.25/0.75) for refined
  premium/discount grading.

## Sources

- [ICT dealing range guide — arongroups.co](https://arongroups.co/technical-analyze/ict-dealing-range/)
- [Dealing range explained — thesimpleict.com](https://thesimpleict.com/dealing-range-ict-guide/)
- [Premium & discount + equilibrium — arongroups.co](https://arongroups.co/technical-analyze/ict-equilibrium-zones/)
