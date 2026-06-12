---
name: draw-on-liquidity
aliases: [DOL, draw]
category: daily-bias
related: [daily-bias, buyside-sellside-liquidity, internal-external-range-liquidity, fair-value-gap, ipda-lookbacks]
parameters:
  candidate_levels: "old daily/weekly highs & lows, relative equal H/L, unfilled FVGs/voids, NWOG/NDOG, session highs/lows"
  lookback: "20/40/60 trading days (IPDA ranges)"
detection: not-implemented
---

# Draw on Liquidity (DOL)

The specific level price is currently being "drawn" toward — the magnet for the next
delivery leg. Every move in the ICT framework is from one liquidity/imbalance objective
to the next; the DOL answers *where is price going*, while bias answers *which way*.

Candidate draws, in rough order of gravity:

- **External range liquidity** — old highs (buy stops) and old lows (sell stops) of the
  active dealing range, including previous day/week/month extremes.
- **Relative equal highs/lows** — engineered pools; the more touches and the cleaner the
  level, the stronger the magnet.
- **Internal range liquidity** — unfilled FVGs, liquidity voids, opening gaps
  (NWOG/NDOG) inside the range.
- **Session levels** — Asia range high/low, London high/low, NY pre-market high/low.

Alternation principle: price runs **external → internal → external** — after taking a
range extreme it rebalances an internal imbalance, then targets the next extreme.

## Detection Rules

- Build a level table each day from the candidate list above, tagged with type, price,
  timestamp created, and `taken` flag.
- DOL = nearest *untaken* level in the bias direction with meaningful size
  (e.g., a pool not already swept within the IPDA 20-day window).
- A level is `taken` once price trades through it by >= 1 tick; equal-high/low pools are
  taken when the highest/lowest of the cluster is violated.
- Invalidation: if the opposing pool is taken with displacement first, re-evaluate bias.

## Sources

- [ICT Daily Bias Explained — innercircletrader.net](https://innercircletrader.net/tutorials/ict-daily-bias-explained/)
- [IPDA: how it frames liquidity & imbalance — arongroups.co](https://arongroups.co/technical-analyze/understanding-how-ipda-frames-liquidity-imbalance-and-institutional-price-delivery/)
- [Daily Bias & DOL rules — tradingfinder.com](https://tradingfinder.com/education/forex/ict-daily-bias/)
