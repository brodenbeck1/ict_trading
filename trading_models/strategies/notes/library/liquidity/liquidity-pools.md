---
name: liquidity-pools
aliases: [session liquidity, PDH, PDL, session highs lows]
category: liquidity
related: [buyside-sellside-liquidity, sessions-and-ranges, draw-on-liquidity, relative-equal-highs-lows]
parameters:
  session_windows_utc: "Asia 18:00-00:00 (prev evening), London 03:00-08:00, NY pre 08:00-13:30, NY RTH 13:30-20:00 (project convention)"
detection: partial   # SwingPointScanner in trading_models/liquidity_pools/swing_points.py
---

# Liquidity Pools (Session & Reference Levels)

Discrete, widely-watched levels where stops cluster. The recurring intraday set:

- **Previous day high / low (PDH / PDL)** — the most universal stop-hunt targets.
- **Asia range high / low** — built 18:00–00:00 UTC; classic target of the London
  manipulation move.
- **London high / low** — often one of these becomes the day's extreme; NY frequently
  runs the London-session extreme before reversing.
- **NY pre-market high / low** (08:00–13:30 UTC) — targeted around the 9:30 equity open.
- **Previous week high / low**, monthly high/low — higher-timeframe magnets.
- **Midnight/weekly opens** — reference prices rather than pools, but price reacts there.

These pools are both **targets** (draws on liquidity) and **setup triggers** (sweep of
a pool → reversal model engages).

## Detection Rules

- At each session boundary, record `session_high`, `session_low` with timestamps.
- Maintain a live level table: {level_type, price, created_at, swept_at, sweep_direction}.
- PDH/PDL computed from the full prior trading day (project: use RTH or full session
  consistently — pick one and record it as a config flag).
- Sweep event: `high[t] > level >= high[t-1]` (for highs) during a later session.

## Sources

- [ICT Liquidity Pool — innercircletrader.net](https://innercircletrader.net/tutorials/ict-liquidity-pool/)
- [Liquidity trading strategy — icttrading.org](https://icttrading.org/ict-liquidity-trading-strategy/)
- [Day 4: Liquidity — tradingstrategyguides.com](https://tradingstrategyguides.com/liquidity-ict-smc-trading-explained/)
