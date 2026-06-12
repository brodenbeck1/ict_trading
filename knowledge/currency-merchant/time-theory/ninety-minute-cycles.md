---
name: ninety-minute-cycles
aliases: [90 minute cycle, 90+ minute equalizer, time cycles]
category: time-theory
related: [cycle-order-flow, session-opens]
ict_refs: [killzones, macros, true-day-midnight-open]
source_coverage: partial-public   # core idea public; Kishane's full "equalizer" treatment is paywalled
parameters:
  base_cycle_start_ny: "2:30 AM"
  cycle_length_min: 90
  tradeable_cycles: "NY AM & PM session cycles (per the public guidance)"
detection: not-implemented
---

# 90-Minute Cycles (The "Equalizer")

The centerpiece of Kishane's **Time Theory**: the trading day is built from repeating
**90-minute algorithmic cycles**, with the base cycle anchored at **2:30 AM NY**.
Each major session (London, NY AM, NY PM) decomposes into consecutive 90-minute
blocks, and each block tends to contain its own complete delivery — its own
manipulation and expansion — making the cycle boundary a recurring decision point.

Working rules from the public material:

- Cycle boundaries (2:30, 4:00, 5:30, 7:00, 8:30, 10:00, 11:30 AM … NY) are when
  delivery "re-arms"; expansions tend to launch near boundaries, not mid-cycle.
- The **previous cycle's high and low** are the live reference levels for the current
  cycle (see [cycle-order-flow](cycle-order-flow.md)).
- Trade the **NY AM and PM cycles**; earlier cycles set up the levels.

Attribution note: 90-minute cycles circulate widely in the post-ICT community
(Zeussy popularized them; Trader Daye's Quarterly Theory formalized a quartered
variant). Kishane's "90+ minute equalizer" is his treatment of the same time
structure — this library records his usage, not a claim of sole authorship.

## Detection Rules

- Cycle grid: timestamps `2:30 AM NY + k * 90min` (DST-safe via America/New_York);
  label cycles by session (London/NY-AM/NY-PM).
- Per-cycle features: OHLC of the cycle, boundary-relative timing of its extreme
  (do extremes cluster early-cycle? — testable), sweep of prior cycle's H/L (bool).
- Research task before building entries on this: measure on ES/NQ/YM whether
  expansion legs disproportionately initiate within ±15 min of cycle boundaries.

## Sources

- [The Currency Merchant Patreon (Time Cycle Maestro) — patreon.com](https://www.patreon.com/TheCurrencyMerchant/about)
- [90-minute cycle times tips — eightify.app](https://eightify.app/summary/trading-strategies/mastering-90-minute-cycle-times-expert-tips-for-successful-trading)
- [90-minute cycles indicator — tradingview.com](https://www.tradingview.com/script/MBeCQZ4G-90-Minute-Cycles/)
- [90+ minute equalizer — instagram.com/@thecurrencymerchant](https://www.instagram.com/reel/DAjbQIjMdj0/)
