---
name: time-over-price
aliases: [time > price, timing principle]
category: core
related: [timing-protocol, quality-protocols]
ict_refs: [killzones, macros]
parameters: {}
detection: not-implemented
---

# Time Over Price ("Time > Price")

The Currency Merchant's filtering principle: **when matters more than where**. A
textbook-perfect range purge at a dead hour is lower probability than a mediocre one
at a key time, because the algorithmic volatility injections that resolve ranges
happen on the clock — session opens, killzone boundaries, and the recurring key hours
(see [timing-protocol](../protocols/timing-protocol.md)).

Practical consequences:

- CRT candidates are pre-filtered by *when the range candle opens* (the 1am/5am/9am
  NY 4H candles) before price is even considered.
- Purges are graded by *when the purge happens* — a sweep during London or NY AM
  carries delivery intent; an overnight drift through a level usually doesn't.
- This is the CRT cousin of ICT's "time gates price" killzone doctrine, promoted from
  filter to first-class ranking criterion.

## Detection Rules

- Every CRT event (range open, purge, confirmation, entry) carries a NY-local
  timestamp feature.
- Score boost when `purge_time` falls in London (2–5 AM) or NY AM (8:30–11 AM)
  windows; score penalty outside all key windows.
- Backtest research task: stratify purge outcomes by hour-of-day to validate/calibrate
  the claimed time hierarchy on ES/NQ/YM.

## Sources

- [Mastering CRT (Time > Price protocol) — scribd.com](https://www.scribd.com/document/898327293/Crt)
- [CRT killzone alignment — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
