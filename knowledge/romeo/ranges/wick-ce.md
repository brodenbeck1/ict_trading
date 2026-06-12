---
name: wick-ce
aliases: [wick consequent encroachment, wick 50%, body midpoint]
category: ranges
related: [candle-range-principle, purge, targets]
ict_refs: [consequent-encroachment, rejection-block, fair-value-gap]
parameters:
  levels: "wick CE = 50% of each wick; body CE = 50% of the body; range CE = 50% of high-low"
detection: not-implemented
---

# Wicks & Consequent Encroachment

In CRT, wicks are first-class objects: a long wick is treated as a **one-sided
inefficiency** (akin to an FVG) left by a rejection, and price tends to revisit it.
The key internal levels of any candle:

- **Range CE** — 50% of high→low: the candle's equilibrium and the first delivery
  target after a purge.
- **Wick CE** — 50% of each wick: the reaction level inside the inefficiency; deep
  retests into a purge wick commonly hold at the wick's CE (measure the fib 0→1 over
  the wick alone).
- **Body CE** — 50% of open→close: the defended midpoint of the delivered portion.

These map directly onto ICT equivalents (consequent encroachment, rejection block)
— CRT just systematizes them per-candle. Practical use: entry refinement (limit at
the purge wick's CE rather than the range extreme) and target laddering (opposing
wick CE before the opposing extreme).

## Detection Rules

- Per candle: `upper_wick = (max(o,c), h)`, `lower_wick = (l, min(o,c))`;
  `wick_ce = midpoint` of each; emit only when wick length >= k × body or >= x
  points (significance filter).
- Post-purge retest logic: entry zone = purge wick; preferred fill = wick CE; stop
  beyond wick extreme.
- Target ladder per CRT: [range CE, opposing wick CE (if any), opposing extreme].

## Sources

- [CRT wick CE — smartmoneyict.com](https://smartmoneyict.com/ict-candle-range-theory/)
- [Wicks require special consideration — theicttrader.com](https://theicttrader.com/2024/03/05/wicks-require-special-consideration/)
- [CRT overview — scribd.com](https://www.scribd.com/document/888159150/Candle-Range-Theory-CRT)
