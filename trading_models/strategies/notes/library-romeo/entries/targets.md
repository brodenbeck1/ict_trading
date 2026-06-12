---
name: targets
aliases: [CRT targets, 50% target, opposing extreme]
category: entries
related: [crt-range, wick-ce, purge, stops-invalidation]
ict_refs: [targets-and-exits, draw-on-liquidity]
parameters:
  ladder: ["TP1: range 50% (CE)", "TP2: opposing extreme", "runner: liquidity beyond the opposing extreme / next HTF objective"]
detection: not-implemented
---

# Targets

CRT targeting is mechanical because the range defines it:

1. **TP1 — the range 50%**: after a purge, the first draw is the midpoint of the
   range (the source phrasing: "the 50% of the opposing end"). Common management:
   take partials and move stop to entry here.
2. **TP2 — the opposing extreme**: the other side of the CRT, where the opposite
   liquidity pool rests. The standard full-target.
3. **Runner — beyond the range**: if the opposing extreme purges *out* (delivery
   continues), the next objective comes from the higher-timeframe context (next HTF
   key level / draw per the ICT-library logic).

Refinement from the wick analysis: when the opposing side of the range has a
significant wick, its **wick CE** is an intermediate ladder rung before the extreme.
Minimum-quality gate: if entry-to-TP2 doesn't clear the R:R threshold against the
purge-wick stop, the setup is skipped.

## Detection Rules

- Ladder computed at entry from CRT state: `[mid, opposing_wick_ce?, opposing_extreme]`.
- Config: partial fractions per rung, breakeven rule after TP1, `min_rr` gate vs TP2.
- Exit codes: `tp1_partial`, `tp2`, `runner`, `stop`, `invalidation`, `eod` — keep
  compatible with the project trade-log schema.
- Research metric: fraction of purges reaching mid vs opposite extreme, by protocol
  score (links quality protocols to expectancy).

## Sources

- [CRT targets (50% rule) — scribd.com](https://www.scribd.com/document/898327293/Crt)
- [CRT take profit — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
- [CRT trading guide — traderfactor.com](https://traderfactor.com/what-is-the-candle-range-theory-strategy/)
