---
name: liquidity-sweep-stop-hunt
aliases: [stop hunt, liquidity sweep, stop raid, purge, liquidity grab]
category: liquidity
related: [buyside-sellside-liquidity, relative-equal-highs-lows, market-structure-shift, turtle-soup, judas-swing]
parameters:
  rejection_window_bars: "bars allowed between the sweep and the close back inside (e.g., 1-12 on 5m)"
  sweep_vs_run_rule: "close back inside the level = sweep (reversal); acceptance beyond = run (continuation)"
detection: implemented
---

# Liquidity Sweep / Stop Hunt

Price trades **beyond** a liquidity pool (old high/low, equal highs/lows, session
extreme), triggers the resting stops, then **reverses back inside** the prior range.
The sweep fills institutional orders against the triggered stops; the swift rejection
is the footprint that the level was raided for liquidity, not broken for continuation.

Critical distinction:

- **Sweep (raid)** — wick through the level, close back inside quickly → reversal
  signal; the swept extreme becomes the protected stop level for the new move.
- **Run (liquidity run)** — price trades through and *accepts* beyond the level
  (closes beyond, builds structure) → continuation; do not fade it.

A sweep alone is not an entry — it must be followed by confirmation (market structure
shift + displacement) per the standard entry sequence.

## Detection Rules

- Sweep of a high: `high[t] > pool_level` AND `close[t'] < pool_level` for some
  `t' in [t, t + rejection_window_bars]`.
- Strength features: penetration depth (points beyond level), time spent beyond,
  volume spike on the sweep bar, whether the sweep bar's close is back inside.
- Classify run instead of sweep if price closes beyond the level for >= N consecutive
  bars (e.g., N=3) or breaks the level again after the first rejection.
- Output event: {pool_ref, sweep_time, direction, depth, classification}.

## Sources

- [Liquidity sweep vs liquidity run — innercircletrader.net](https://innercircletrader.net/tutorials/ict-liquidity-sweep-vs-liquidity-run/)
- [What is liquidity in ICT — arongroups.co](https://arongroups.co/technical-analyze/liquidity-in-ict/)
- [Buy/sell side liquidity & stop hunts — writofinance.com](https://www.writofinance.com/buy-side-and-sell-side-liquidity-ict-and-smc/)
