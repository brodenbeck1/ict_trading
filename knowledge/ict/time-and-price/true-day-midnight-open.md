---
name: true-day-midnight-open
aliases: [midnight open, true day, true day open, 8:30 open, opening price]
category: time-and-price
related: [ohlc-candle-profiles, power-of-three, judas-swing, nwog-ndog]
parameters:
  midnight_open_ny: "12:00 AM NY — anchor of the IPDA 'true day'"
  true_day_ny: "12:00 AM - 3:00 PM NY (IPDA true day window)"
  secondary_opens_ny: ["8:30 AM (NY session open used in PO3 intraday)", "9:30 AM (equity cash open)", "6:00 PM (new trading day open / NDOG)"]
detection: not-implemented
---

# True Day & the Midnight Open

ICT's **true day** runs from **midnight NY to ~3:00 PM NY** — the window the IPDA
treats as one delivery cycle; price action after 3 PM is mostly position-squaring, not
fresh delivery. The **midnight open** (12:00 AM NY opening price) is the day's
canonical reference:

- **Bullish day expectation**: the manipulation low forms **below the midnight open**
  (buy at a discount to the open) before expansion higher — and vice versa for bearish
  days. This operationalizes the [OHLC profile](../daily-bias/ohlc-candle-profiles.md).
- The **8:30 AM** and **9:30 AM** opens serve the same role for the NY-session PO3 at
  a smaller scale.
- Distance from the midnight open also gauges chase risk: entries far above it on a
  bullish day are late.

In UTC (project data): midnight NY = 04:00/05:00 UTC; 3 PM NY = 19:00/20:00 UTC.

## Detection Rules

- `midnight_open = first price at/after 00:00 America/New_York` each day (DST-safe).
- Day features: `manipulation_below_open` (bullish days: did low-of-day print below
  midnight open before the high?), `judas_extreme_time`.
- Entry gate (config): `long only if price < midnight_open` during the manipulation
  window; mirror for shorts.
- True-day clipping for backtests: optionally ignore signals after 3 PM NY.

## Sources

- [True day / IPDA day — time-price-research-astrofin.blogspot.com](https://time-price-research-astrofin.blogspot.com/p/off-topic.html)
- [ICT IPDA — innercircletrader.net](https://innercircletrader.net/tutorials/ict-ipda/)
- [Power of 3 (midnight open usage) — innercircletrader.net](https://innercircletrader.net/tutorials/ict-power-of-3/)
