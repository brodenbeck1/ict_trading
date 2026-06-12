---
name: smt-divergence
aliases: [SMT, smart money technique, smart money divergence, crack in correlation]
category: entries
related: [liquidity-sweep-stop-hunt, market-structure-shift, entry-sequence]
parameters:
  instruments: "ES, NQ, YM (project: all three required in MarketSnapshot.correlated)"
  comparison_timeframe: "15m or lower for execution; same timeframe on both charts"
  swing_window: "compare corresponding swing extremes within a small time tolerance (e.g., +/- 3 bars)"
detection: not-implemented
---

# SMT Divergence (Smart Money Technique)

A **crack in correlation** between positively correlated instruments: one makes a new
swing extreme while the other(s) fail to confirm. At a low: NQ prints a lower low
(sweeping sell stops) while ES holds a higher low → the sweep on NQ was engineered,
not genuine weakness — bullish signal. At a high: one prints a higher high while the
other makes a lower high → bearish.

ES/NQ is the canonical futures pair (tight correlation, predictable delivery); YM as a
third vote raises confidence. Instrument-selection rule from the forex-era teaching
carries over: **trade the instrument that refused to confirm** — at a low, buy the one
that held the higher low (demand in operation); at a high, sell the one that failed to
make the higher high (supply in operation). SMT is a **confirmation layer, not a standalone signal**:
it grades a sweep (sweep + SMT > sweep alone) and is strongest when it appears at a
HTF PD array inside a killzone, alongside an MSS.

Project convention: requires all three of ES/NQ/YM in `MarketSnapshot.correlated`;
per the elements-of-a-trade-setup decision, SMT is layered into separate models, not
the base model.

## Detection Rules

- Align both series on the same resampled index (UTC).
- At a candidate sweep low on instrument A at time t: find instrument B's
  corresponding swing low within ±tolerance bars.
- Bullish SMT: `A.low[t] < A.prior_swing_low` AND `B.low[t'] > B.prior_swing_low`
  (use matched prior swings, e.g., both from the same prior session extreme).
- Emit {time, pair, divergence_type, leader (which swept), levels}; expire if the
  non-confirming instrument later takes its level anyway (divergence negated).

## Sources

- [ICT SMT divergence — innercircletrader.net](https://innercircletrader.net/tutorials/ict-smt-divergence-smart-money-technique/)
- [SMT in futures (ES/NQ) — metrotrade.com](https://www.metrotrade.com/smt-trading-futures/)
- [SMT identification — tradingfinder.com](https://tradingfinder.com/education/forex/ict-smt-divergence/)
- Stronger/weaker selection rule: `strategies/notes/ict-forex-notes-mmari-2020.md` §6
