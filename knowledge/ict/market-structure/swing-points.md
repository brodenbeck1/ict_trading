---
name: swing-points
aliases: [swing high, swing low, STH, STL, ITH, ITL, LTH, LTL, fractal]
category: market-structure
related: [break-of-structure, market-structure-shift, buyside-sellside-liquidity, dealing-range]
parameters:
  swing_definition: "3-bar (project decision): bar N is a swing low if low[N] < low[N-1] and low[N] < low[N+1]; mirror for highs"
  confirmation_lag: "1 bar (3-bar swing confirms one bar after the pivot)"
detection: implemented   # src/ict/concepts/market_structure.py (@concept("swing-points"))
---

# Swing Points

The atomic structural unit. A **swing high** is a bar whose high exceeds its neighbors;
a **swing low** is a bar whose low undercuts its neighbors. Project standard is the
3-bar definition (decided 2026-06-06).

ICT layers a hierarchy on top:

- **Short-term high/low (STH/STL)** — a plain 3-bar swing.
- **Intermediate-term high/low (ITH/ITL)** — a swing high that is higher than the
  swing highs on both sides of it (a swing of swings).
- **Long-term high/low (LTH/LTL)** — an intermediate swing that dominates the
  intermediate swings around it.

This hierarchy ranks liquidity pools (LT extremes carry more stops) and defines which
break constitutes a meaningful structure event vs. noise.

## Detection Rules

- 3-bar pivot as in parameters; a swing is only *confirmed* after the right-side bar
  closes (avoid lookahead in backtests — signal time = close of bar N+1).
- Build the ST list; derive IT swings by applying the same pivot test to the ST series;
  derive LT from IT.
- Every confirmed swing emits a liquidity tag (BSL at highs, SSL at lows).
- Optional strength filter: minimum prominence in points/ATR to drop micro-swings on 1m.

## Sources

- [Market structure shift guide — innercircletrader.net](https://innercircletrader.net/tutorials/ict-market-structure-shift/)
- Project decision log: `strategies/notes/ict-elements-of-a-trade-setup.md` (3-bar swing)
- Project code: `src/ict/concepts/market_structure.py`
