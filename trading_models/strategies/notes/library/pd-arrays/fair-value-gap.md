---
name: fair-value-gap
aliases: [FVG, imbalance, SIBI, BISI]
category: pd-arrays
related: [displacement, inversion-fvg, balanced-price-range, liquidity-void, consequent-encroachment]
parameters:
  min_gap_size: "points; project decision: 0 (any gap qualifies)"
  entry_edge: "limit at the near edge of the gap (project decision: top of FVG for shorts, bottom for longs)"
  mitigation_rule: "touched = partially mitigated; full fill = rebalanced; close beyond = inverted"
detection: not-implemented
---

# Fair Value Gap (FVG)

The atomic three-candle imbalance. During a displacement candle (candle 2), price moves
so fast that candle 1's and candle 3's wicks never overlap, leaving a gap where only
one-sided delivery occurred:

- **Bullish FVG (BISI** — buy-side imbalance, sell-side inefficiency**)**:
  `low[3] > high[1]`; zone = (high[1], low[3]).
- **Bearish FVG (SIBI** — sell-side imbalance, buy-side inefficiency**)**:
  `high[3] < low[1]`; zone = (high[3], low[1]).

The FVG is both a **magnet** (price returns to rebalance the inefficiency) and a
**reaction zone** (the algorithm defends gaps created by its own displacement). The
standard entry pattern across nearly all ICT models: sweep → MSS with displacement →
limit order in the FVG the displacement created.

The gap's 50% line ([consequent encroachment](consequent-encroachment.md)) is the key
internal level: strong setups often fill only to CE before continuing.

## Detection Rules

- For each bar i: bullish FVG if `low[i] > high[i-2]`; zone `(high[i-2], low[i])`,
  created at close of bar i. Mirror for bearish.
- Filters (config): minimum gap height in points or ATR fraction; require the middle
  candle to qualify as displacement.
- State: `fresh → tested (any trade into zone) → rebalanced (full traverse) →
  inverted (close beyond far edge)` — see [inversion-fvg](inversion-fvg.md).
- Direction-of-use: bullish FVG below price = discount support; bearish FVG above =
  premium resistance.

## Sources

- [FVG strategy & family — innercircletrader.net](https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/)
- [Complete FVG guide — writofinance.com](https://www.writofinance.com/fair-value-gap-in-trading/)
- [FVG trading strategy — trendspider.com](https://trendspider.com/learning-center/fair-value-gap-trading-strategy/)
- Project decision log: `strategies/notes/ict-elements-of-a-trade-setup.md`
