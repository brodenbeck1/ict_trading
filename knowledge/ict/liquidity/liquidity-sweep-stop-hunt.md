---
name: liquidity-sweep-stop-hunt
aliases: [stop hunt, liquidity sweep, stop raid, purge, liquidity grab]
category: liquidity
related: [buyside-sellside-liquidity, relative-equal-highs-lows, market-structure-shift, turtle-soup, judas-swing]
parameters:
  rejection_window_bars: "bars allowed between the sweep and the close back inside (e.g., 1-12 on 5m)"
  sweep_vs_run_rule: "close back inside the level = sweep (reversal); acceptance beyond = run (continuation)"
  pool_validity: "a pool is live only until its FIRST breach since it formed; that first raid is the liquidity grab — later revisits of an already-run level are invalid"
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

- **Pool must still be live (first-breach rule).** The first time price trades beyond
  a level *since it formed* is the moment the resting liquidity is taken. A valid
  sweep must BE that first breach. If the level was first run earlier — on a prior
  session, or outside the killzone — the pool is dead (mitigated) and any later poke
  is price revisiting a spent level, not a fresh grab. Each pool therefore carries a
  `formed_at` timestamp, and the breach search starts strictly after it (the pool's
  own formation must not self-trigger). Implemented as `first_breach()` /
  `pool_is_live()` in `src/ict/concepts/liquidity_sweep.py`.
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
