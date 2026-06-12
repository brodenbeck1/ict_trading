---
name: liquidity-void
aliases: [void, multi-candle imbalance]
category: liquidity
related: [fair-value-gap, displacement, balanced-price-range, internal-external-range-liquidity]
parameters:
  min_candles: 2
  fill_rule: "void is rebalanced when price retraces through its full height (or to consequent encroachment 50%)"
detection: not-implemented
---

# Liquidity Void

A **multi-candle** one-sided imbalance: price breaks out of consolidation and travels
in one direction with little or no overlap between successive candles, leaving a zone
where two-way trade never occurred. A void can span many candles and typically
*contains* one or more fair value gaps; think of the FVG as the 3-candle atomic unit
and the void as the extended version.

Behavior: voids act as low-resistance corridors. Price tends to retrace through a void
quickly (nothing to slow it down) until it reaches the origin of the move or an
embedded PD array. An unfilled void inside a range is internal range liquidity — a
standing draw.

## Detection Rules

- Scan for sequences of `k >= min_candles` same-direction candles where each candle's
  range has minimal overlap with the prior (e.g., `low[i] > high[i-2]` chained for
  bullish runs).
- Void zone = from the consolidation breakout price to the end of the displacement leg.
- Track fill fraction: % of void height retraced; mark `rebalanced` at 100% (or at 50%
  consequent encroachment as a softer rule — config flag).
- Distinguish from FVG in outputs: `type: void` with `contained_fvgs: [...]`.

## Sources

- [ICT liquidity void — innercircletrader.net](https://innercircletrader.net/tutorials/master-ict-liquidity-void/)
- [Liquidity void meaning & setup — arongroups.co](https://arongroups.co/technical-analyze/liquidity-void-in-ict/)
- [FVG vs liquidity void — fxopen.com](https://fxopen.com/blog/en/fair-value-gaps-vs-liquidity-voids-in-trading/)
