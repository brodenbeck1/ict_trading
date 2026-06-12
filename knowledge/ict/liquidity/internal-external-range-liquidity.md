---
name: internal-external-range-liquidity
aliases: [IRL, ERL, internal range liquidity, external range liquidity]
category: liquidity
related: [dealing-range, fair-value-gap, draw-on-liquidity, premium-discount]
parameters: {}
detection: not-implemented
---

# Internal vs External Range Liquidity (IRL / ERL)

Within an active [dealing range](../market-structure/dealing-range.md):

- **External range liquidity (ERL)** — the stops resting beyond the range extremes:
  buy stops above the range high, sell stops below the range low.
- **Internal range liquidity (IRL)** — imbalances *inside* the range: fair value gaps,
  liquidity voids, order blocks, opening gaps that price still owes a revisit.

The alternation principle is one of the most mechanically useful ICT ideas:
**price rotates ERL → IRL → ERL**. After taking a range extreme, price typically
retraces to rebalance an internal imbalance (IRL); after filling internal imbalance,
it expands to the next external pool. This gives a standing answer to "what's the
current draw?": whichever type was taken last, the other is next.

## Detection Rules

- Define the dealing range (significant swing high ↔ swing low, or IPDA 20-day range).
- ERL events: trade through `range.high` or `range.low`.
- IRL events: trade into an unmitigated FVG/void inside the range (typically on the
  higher timeframe — 1H/4H/daily).
- State machine per range: `last_taken in {ERL_high, ERL_low, IRL}` → next expected
  objective; combine with bias to pick direction (bullish bias + IRL just filled →
  target ERL high).

## Sources

- [ICT dealing range & market structure — arongroups.co](https://arongroups.co/technical-analyze/ict-dealing-range/)
- [Dealing range, ERL/IRL — thesimpleict.com](https://thesimpleict.com/dealing-range-ict-guide/)
- [PD arrays & ranges — fxopen.com](https://fxopen.com/blog/en/what-is-a-pd-array-in-ict-and-how-can-you-use-it-in-trading/)
