---
name: sessions-and-ranges
aliases: [asian range, CBDR, central bank dealers range, london session, ny session]
category: time-and-price
related: [killzones, liquidity-pools, power-of-three, true-day-midnight-open]
parameters:
  asian_range_ny: "8:00 PM - 12:00 AM (ICT forex definition); project UTC convention: 18:00-00:00"
  cbdr_ny: "2:00 PM - 8:00 PM (between NY close and Asia open)"
  flout_ny: "3:00 PM - 12:00 AM (CBDR + Asia, used for projections)"
detection: not-implemented
---

# Sessions & Reference Ranges

Beyond killzones, ICT defines measured **ranges** whose highs/lows become the day's
liquidity scaffolding:

- **Asian Range** — ICT: 8:00 PM–midnight NY (project convention: 18:00–00:00 UTC).
  The quiet accumulation range; its high/low are the first manipulation targets in
  London. Range height also gauges overnight volatility.
- **CBDR (Central Bank Dealers Range)** — 2:00–8:00 PM NY. A forex-centric concept:
  when the CBDR is tight (ideally 20–30 pips FX), its height is projected in standard
  deviations (±1, ±2, ±4...) above/below to estimate where the day's high/low may form.
  For index futures, the analogous use is projecting the afternoon/overnight
  consolidation height.
- **Flout** — CBDR + Asia combined (3 PM–midnight), alternative projection base.
- **Session highs/lows** — London H/L, NY pre-market H/L: standing intraday pools
  (see [liquidity-pools](../liquidity/liquidity-pools.md)).

## Detection Rules

- Compute ranges as `(max(high), min(low))` over the session mask (NY-local windows
  converted to UTC per date).
- Standard-deviation projections: `proj_k = range_high + k * range_height` (and mirror
  below); store k in {1, 2, 2.5, 4} for confluence with other targets.
- Feature flags per day: `asia_range_height`, `asia_high_taken_by` (session),
  `london_made_day_extreme` (bool — for profile classification).

## Sources

- [Killzones & session times — innercircletrader.net](https://innercircletrader.net/tutorials/master-ict-kill-zones/)
- [Time & price research (CBDR, Asia, flout) — time-price-research-astrofin.blogspot.com](https://time-price-research-astrofin.blogspot.com/p/off-topic.html)
- Project convention: CLAUDE.md session windows (UTC)
