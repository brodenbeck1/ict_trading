---
name: premium-discount
aliases: [equilibrium, EQ, premium array, discount array, 50% level]
category: pd-arrays
related: [dealing-range, optimal-trade-entry, pd-array-matrix, internal-external-range-liquidity]
parameters:
  equilibrium: 0.5
  quartiles: [0.25, 0.75]
detection: implemented
---

# Premium / Discount & Equilibrium

Within any [dealing range](../market-structure/dealing-range.md), the 50% level
(**equilibrium**) splits price into:

- **Premium** (above EQ) — expensive; the zone where institutions *sell*. With bearish
  bias, entries are only valid in premium.
- **Discount** (below EQ) — cheap; the zone where institutions *buy*. Bullish entries
  only in discount.

This is the simplest and most universal ICT filter: **never buy in premium, never sell
in discount**. It's a Fibonacci tool dragged low-to-high of the range with only the
0.5 line — no indicator needed. Refinements: the deeper quartiles (above 0.75 / below
0.25) are "deep premium/discount" where reversal arrays carry the most weight, and the
[OTE zone](../entries/optimal-trade-entry.md) (62–79% retracement) is the premium/
discount sweet spot of an individual leg.

## Detection Rules

- `eq = (range_high + range_low) / 2`; `position = (price - range_low) / (range_high - range_low)`.
- Gate: `if direction == long: require position < 0.5` (optionally < 0.35 for deep
  discount); mirror for shorts.
- Targets respect the same logic: longs from discount target premium arrays/ERL;
  first objective often the EQ itself, then the opposing quartile.
- Track per-timeframe: a 5m discount inside a daily premium is still a countertrend
  long — models should state which range governs.

## Sources

- [Premium vs discount — thesimpleict.com](https://thesimpleict.com/premium-vs-discount-ict-smart-money/)
- [Equilibrium zones — arongroups.co](https://arongroups.co/technical-analyze/ict-equilibrium-zones/)
- [PD array matrix — writofinance.com](https://www.writofinance.com/ict-pd-array-matrix-in-forex/)
