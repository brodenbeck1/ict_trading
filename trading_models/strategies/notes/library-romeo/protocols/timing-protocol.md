---
name: timing-protocol
aliases: [key times, CRT times, 1-5-9]
category: protocols
related: [time-over-price, quality-protocols, purge, fractal-timeframe-pairing]
ict_refs: [killzones, macros, sessions-and-ranges]
parameters:
  key_times_ny: ["1:00 AM", "5:00 AM", "9:00 AM", "1:00 PM", "3:00 PM (some sources 5:00 PM)", "9:00 PM"]
  primary_4h_candles_ny: ["1:00 AM", "5:00 AM", "9:00 AM"]
  calendar_emphasis: "Mondays & Fridays; first week of the month (per source material)"
detection: not-implemented
---

# Timing Protocol (Key Times)

The specific clock times CRT treats as algorithmic decision points — both for **which
range candles matter** (the 4H candles *opening* at these times) and **when purges
are trustworthy**:

- **1:00 AM NY** — pre-London 4H candle; its range frames the London manipulation.
- **5:00 AM NY** — London 4H candle; purges of the 1 AM range resolve here.
- **9:00 AM NY** — the NY 4H candle; the prime index window (contains 9:30 open,
  8:30 data drops just before, and the 10–11 macros).
- **1:00 PM / 3:00 PM / 9:00 PM NY** — afternoon and Asia-handoff candles; secondary.

These align with London/NY killzones and ICT macro windows — same market physics,
expressed as candle-open times. Sources mostly quote EST/EDT loosely; treat all as
**NY local** and convert per-date.

## Detection Rules

- Key-time mask on candle open times in `America/New_York` (DST-safe), per timeframe.
- 4H resampling for this project's UTC data must be anchored so candles open at
  1/5/9 NY (e.g., EDT ⇒ opens at 05/09/13/17/21/01 UTC ⇒ `resample('4H', offset='1h')`;
  re-derive under EST). **Do not use the default UTC-midnight 4H grid.**
- Protocol flags per CRT: `range_opened_at_key_time`, `purged_at_key_time`,
  `purge_in_killzone`; calendar features: day-of-week, week-of-month.

## Sources

- [4H CRT (1AM and 5AM) indicator — tradingview.com](https://www.tradingview.com/script/kXR0vkG2-4H-CRT-1AM-and-5AM/)
- [Key timing 1/5/9/1/3/9 NY — threads.com/@smcandict](https://www.threads.com/@smcandict/post/DAWUyiQC-W6?hl=en)
- [Mastering CRT (timing) — scribd.com](https://www.scribd.com/document/898327293/Crt)
