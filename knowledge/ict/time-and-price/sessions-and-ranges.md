---
name: sessions-and-ranges
aliases: [asian range, CBDR, central bank dealers range, london session, ny session]
category: time-and-price
related: [killzones, liquidity-pools, power-of-three, true-day-midnight-open]
parameters:
  asian_range_ny: "8:00 PM - 12:00 AM (ICT forex definition); project UTC convention: 18:00-00:00"
  cbdr_ny: "2:00 PM - 8:00 PM (between NY close and Asia open)"
  flout_ny: "3:00 PM - 12:00 AM (CBDR + Asia, used for projections)"
  opening_range_start: "09:30"   # NY start of the opening range (RTH cash open); e.g. 08:30 for the NY session-open range
  opening_range_minutes: 30
  ons_ny: "05:00 – 09:15"        # Overnight Session — pre-market window from globex overnight to RTH open
  chicago_ny: "09:15 – 12:00"   # Chicago session — CME pit open to midday; pools sweepable PM same-day or next-day
detection: implemented
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
- **Overnight Session (ONS)** — **05:00–09:15 NY**. The pre-market window from
  globex overnight through to the RTH open. Its high/low are standing intraday
  liquidity pools, often swept in the opening killzone or early RTH. Implemented
  as `ons_range()` in `src/ict/concepts/sessions.py`.
- **Chicago Session** — **09:15–12:00 NY**. CME pit session open through midday.
  Its high/low are liquidity pools once the window closes (`formed_at = range_end`).
  Two uses: (1) **same-day** — sweepable in the PM killzone (13:30–16:00 NY);
  (2) **next-day** — carried forward as a standing pool alongside PDH/PDL, available
  from the next session open. Implemented as `chicago_range()` in
  `src/ict/concepts/sessions.py`.
- **Opening Range (OR)** — the first 30 min after the **09:30 NY cash open** (RTH OR,
  the project default for `opening_range`); its high/low are intraday liquidity pools.
  `start_ny` can anchor the range to another session open (e.g. `08:30` for the NY
  session open). The OR is a **range** (high/low) — distinct from the **midnight open**,
  which is a single reference *price* (the true-day open), not a range; see
  [true-day-midnight-open](true-day-midnight-open.md). As a pool, the OR only *exists*
  once the range closes — it must never be treated as swept before its `range_end`
  (no look-ahead; see [liquidity-sweep-stop-hunt](../liquidity/liquidity-sweep-stop-hunt.md)).
- **Session highs/lows** — London H/L, NY pre-market H/L: standing intraday pools
  (see [liquidity-pools](../liquidity/liquidity-pools.md)).

**Flout projection recipe (2020 forex-era variant)** — the Mmari notes define the
"flout" as the 20:00–00:00 GMT consolidation and measure the projection base off
candle **bodies** (wicks ignored) over 20:00–05:00 GMT: the day's high (sell days)
forms ≈ **+1 range-height deviation** above the base, the target/low ≈ **−2 deviations**
(reversal-profile days stretch to ±2 entry / −3 target). Best Monday–Wednesday; no
trades inside the base window. Note the window conflicts with the NY-time CBDR/flout
definitions above — those stay canonical; keep this as the deviation-count reference.

**5-day ADR targeting** (same source): align trade expectations to the 5-day average
daily range — 5 contracted days ⇒ expect expansion; take profit at 80–90% of ADR
rather than the extreme; if ADR is exceeded, fib the ADR low→high for extensions.

## Detection Rules

- Compute ranges as `(max(high), min(low))` over the session mask (NY-local windows
  converted to UTC per date).
- Overnight Session (ONS): high/low over `05:00–09:15` NY via `ons_range()`. Live pools
  from `range_end`.
- Chicago Session: high/low over `09:15–12:00` NY via `chicago_range()`. Same-day pool
  with `formed_at = range_end` (noon); also carried as a next-day pool (`formed_at =
  session_open`, like PDH/PDL). Sweepable in PM killzone (13:30–16:00 NY) same-day.
- Opening range: high/low over `[start_ny, start_ny + minutes)` in NY local time
  (default `09:30` + 30 min). It becomes a sweepable pool only at `range_end`.
- Standard-deviation projections: `proj_k = range_high + k * range_height` (and mirror
  below); store k in {1, 2, 2.5, 4} for confluence with other targets.
- Feature flags per day: `asia_range_height`, `asia_high_taken_by` (session),
  `london_made_day_extreme` (bool — for profile classification).

## Sources

- [Killzones & session times — innercircletrader.net](https://innercircletrader.net/tutorials/master-ict-kill-zones/)
- [Time & price research (CBDR, Asia, flout) — time-price-research-astrofin.blogspot.com](https://time-price-research-astrofin.blogspot.com/p/off-topic.html)
- Project convention: CLAUDE.md session windows (UTC)
- Flout deviations & ADR: `strategies/notes/ict-forex-notes-mmari-2020.md` §16 (2020 forex-era ICT)
