---
name: stops-invalidation
aliases: [CRT stop loss, purge wick stop]
category: entries
related: [purge, entry-triggers, targets]
ict_refs: [stop-placement]
parameters:
  standard_stop: "a few ticks beyond the purge wick extreme"
  hard_invalidation: "range-tf close beyond the purged extreme kills the idea regardless of stop"
detection: not-implemented
---

# Stops & Invalidation

The purge wick is the protected extreme. Once the raid is complete, the methodology's
premise is that the algorithm will not revisit it before delivering to the opposite
side — so:

- **Stop**: a few ticks beyond the purge wick (below the wick low for longs). Same
  structural-invalidation logic as the ICT
  [stop-placement](../../ict/entries/stop-placement.md) convention.
- **Hard invalidation** (independent of the stop): a **range-timeframe close beyond
  the purged extreme**. That converts the purge into a breakout — the CRT read was
  wrong, and any surviving position should be closed even if the LTF stop hasn't
  been tagged.
- Wider variant for daily CRTs: stop beyond the *opposing* side of the purge candle
  (the manipulation candle's full range) — used when the entry is at the wick CE and
  the wick is deep.

Risk per trade derives from stop distance; CRT stop distances are naturally small
relative to the target (range width), which is where the model's R-multiple claims
come from — verify in backtest rather than assume.

## Detection Rules

- `stop = purge_extreme ± buffer_ticks`.
- Monitor range-tf closes while in trade: `close beyond purged extreme → exit_reason
  = invalidation` (distinct code from `stop` in the trade log).
- Log `stop_distance_pts`, `stop_distance_pct_of_range` for results normalization.

## Sources

- [CRT stop placement — tradingfinder.com](https://tradingfinder.com/education/forex/ict-candle-range-theory/)
- [CRT guide — writofinance.com](https://www.writofinance.com/candle-range-theory-crt/)
