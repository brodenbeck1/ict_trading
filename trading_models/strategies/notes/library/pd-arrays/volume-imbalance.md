---
name: volume-imbalance
aliases: [VI, opening gap candle imbalance]
category: pd-arrays
related: [fair-value-gap, nwog-ndog, liquidity-void]
parameters: {}
detection: not-implemented
---

# Volume Imbalance

A gap **between the bodies of two consecutive candles whose wicks still overlap**:
candle 2 opens away from candle 1's close, and no candle body ever printed in between,
even though wicks traded through. Weaker than an FVG (some two-way trade occurred via
the wicks) but still an inefficiency the algorithm tends to re-deliver through.

Hierarchy of single-location inefficiencies, strongest to weakest:
**actual gap** (no trade at all — see [NWOG/NDOG](nwog-ndog.md)) → **FVG** (3-candle,
no wick overlap) → **volume imbalance** (bodies gap, wicks overlap). Volume imbalances
often appear at the edge of displacement legs and refine entry levels inside larger
zones (e.g., a VI at the edge of an order block marks the precise defended line).

## Detection Rules

- Bullish VI between bars i-1, i: `min(open[i], close[i]) > max(open[i-1], close[i-1])`
  AND `low[i] <= high[i-1]` (wicks overlap — otherwise it's a true gap).
- Zone = (top of body 1, bottom of body 2); treat like a thin FVG: magnet + reaction
  line; filled when a body closes through it.
- Use mainly as a refinement/confluence feature, not a standalone entry.

## Sources

- [Key ICT concepts — tradezella.com](https://www.tradezella.com/learning-items/key-ict-concepts)
- [FVG family — innercircletrader.net](https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/)
