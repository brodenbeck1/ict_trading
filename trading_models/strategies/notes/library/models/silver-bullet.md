---
name: silver-bullet
aliases: [SB, silver bullet setup]
category: models
related: [fair-value-gap, killzones, macros, entry-sequence, draw-on-liquidity]
parameters:
  windows_ny: ["3:00-4:00 AM (London)", "10:00-11:00 AM (NY AM)", "2:00-3:00 PM (NY PM)"]
  primary_window_indices: "10:00-11:00 AM NY"
  min_target_handles: "5 handles minimum from FVG entry to target pool (index convention)"
  primary_array: fair-value-gap
detection: not-implemented
---

# Silver Bullet

A strictly **time-boxed FVG model**: the same displacement-FVG-retrace trade, but only
taken inside three specific 60-minute windows — the flagship being **10:00–11:00 AM
NY** for index futures (note it spans the 9:50–10:10 and 10:45–11:15 macros).

Rules:
1. At the window open, identify the current **draw on liquidity** (nearest pool).
2. Wait for **displacement toward that pool to begin inside the window**, leaving an
   FVG. The FVG must be positioned *opposite* the targeted pool (e.g., bullish FVG
   below price when targeting buy-side above).
3. **Entry**: limit at the FVG edge nearest price (top of FVG for longs).
4. **Stop**: beyond the FVG / the displacement origin.
5. **Target**: the identified pool; validate the run is at least ~5 handles (index
   convention), take profit at the pool.

Distinctives: the sweep/MSS requirement is relaxed relative to the 2022 model — time
window + displacement + FVG carry the weight; setups not triggered within the hour
are abandoned.

## Detection Rules

- Window masks in NY-local time (DST-safe).
- Within the window: displacement event (leg with FVG) whose direction points at an
  untaken registry pool; entry order at gap edge; cancel at window close if unfilled.
- Gates: `distance(entry, target_pool) >= min_target_handles`; one trade per window.

## Sources

- [ICT silver bullet — innercircletrader.net](https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/)
- [Silver bullet windows & FVG — fxopen.com](https://fxopen.com/blog/en/what-is-the-ict-silver-bullet-strategy-and-how-does-it-work/)
- [Silver bullet rules — howtotrade.com](https://howtotrade.com/trading-strategies/ict-silver-bullet/)
- [Silver bullet times — ultimamarkets.com](https://www.ultimamarkets.com/academy/ict-silver-bullet-times-to-trade/)
