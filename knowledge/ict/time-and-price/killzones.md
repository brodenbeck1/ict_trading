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
