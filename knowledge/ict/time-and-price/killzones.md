---
name: killzones
aliases: [KZ, london killzone, new york killzone, asian killzone]
category: time-and-price
related: [sessions-and-ranges, macros, power-of-three, silver-bullet]
parameters:
  asia_kz_ny: "7:00-10:00 PM (some sources 8:00 PM-12:00 AM)"
  london_kz_ny: "2:00-5:00 AM"
  ny_kz_indices_ny: "8:30-11:00 AM"
  ny_kz_forex_ny: "7:00-10:00 AM"
  london_close_kz_ny: "10:00 AM-12:00 PM"
  dst_note: "all times are New York local; convert to UTC per-date (EDT=UTC-4, EST=UTC-5)"
detection: not-implemented
---

# Killzones

The recurring windows when institutional order flow concentrates and ICT setups are
expected to form. Trading outside killzones is the most common rookie failure mode —
**time gates price**: the same pattern outside the window is not the same trade.

| Killzone | NY time | Typical role (indices) |
|---|---|---|
| Asia | 7–10 PM | Builds the overnight range/liquidity |
| London | 2–5 AM | Manipulation leg; often forms the day's high or low |
| NY AM | **8:30–11:00 AM** | Primary index window — the project's main hunting ground |
| London Close | 10 AM–12 PM | Reversal/retracement of the London leg |
| NY PM | 1:30–4 PM | Afternoon trend continuation/reversal window |

For ES/NQ/YM, the NY AM killzone (8:30–11:00 NY = 12:30–15:00 / 13:30–16:00 UTC by
DST) matches the project's standard setup window from the elements-of-a-trade-setup
note.

**Source variant (2020 forex-era ICT, GMT)** — the Mmari notes define the windows as
Asian 23:00–03:00, London open 06:00–10:00 (ideal 07:00–09:00), NY open 12:00–15:00,
London close 15:00–18:00 GMT, each ±1 h; the "true trading day" runs 05:00–19:00 GMT
and the day's high/low most often prints **09:00–09:30 GMT** with a counter-move
(Judas) expected around 10:00 GMT. Historical/forex calibration — the NY-time table
above stays canonical for ES/NQ/YM.

## Detection Rules

- Implement as boolean masks over the DatetimeIndex, computed in `America/New_York`
  then converted to UTC — never hardcode UTC clock times (DST shifts them).
- Models take `allowed_killzones: [...]` config; signal generation is suppressed
  outside the mask.
- Backtest slicing: report stats per killzone (extends the project's Asia/London/NY
  session breakdown).

## Sources

- [ICT killzones — all 4 session times — innercircletrader.net](https://innercircletrader.net/tutorials/master-ict-kill-zones/)
- [Killzones explained — tradingrage.com](https://tradingrage.com/learn/ict-killzone-explained)
- GMT variant: `strategies/notes/ict-forex-notes-mmari-2020.md` §9 (2020 forex-era ICT)
