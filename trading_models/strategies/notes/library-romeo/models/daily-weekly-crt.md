---
name: daily-weekly-crt
aliases: [daily CRT, weekly CRT, Monday range]
category: models
related: [three-candle-model, fractal-timeframe-pairing, crt-range, targets]
ict_refs: [weekly-profiles, ohlc-candle-profiles, liquidity-pools]
parameters:
  daily_pair: "daily CRT -> 1H entry; previous day's candle = the range (PDH/PDL purge logic)"
  weekly_pair: "weekly/Monday CRT -> 4H/1H entry; Monday's candle commonly = the week's accumulation range"
detection: not-implemented
---

# Daily & Weekly CRT

The same model at swing scale:

- **Daily CRT**: yesterday's candle is the range — so the classic "purge the previous
  day's high/low then reverse" trade *is* a daily CRT. Pair with 1H entries. The
  three-candle form: accumulation day → manipulation day (wick through PDH/PDL,
  close back inside) → distribution day. This unifies CRT with the PDH/PDL stop-hunt
  logic already in the ICT library.
- **Weekly CRT**: the prior week's candle (or, commonly, **Monday's candle** as the
  intra-week accumulation range). Tuesday's purge of Monday's low in a bullish week
  is the CRT phrasing of the ICT *Tuesday low-of-the-week* profile — the two
  libraries describe the same delivery with different units.
- Calendar emphasis from the source material: Mondays, Fridays, and the first week
  of the month produce the most reliable weekly-scale CRTs.

## Detection Rules

- Daily: CRT = prior completed daily candle (project convention: define the daily
  candle on the 18:00 NY futures day or midnight-to-midnight — pick one config flag
  and keep it fixed); purge/confirmation detected on 1H; targets = daily mid /
  opposite extreme.
- Weekly: CRT = Monday's candle once it closes; purge watched Tue–Wed on 4H/1H;
  delivery expected into Thu; aligns with the weekly-profile classifier in the ICT
  library — share features between the two.
- Both reuse the generic CRT state machine with different `(range_tf, entry_tf)`.

## Sources

- [Daily CRT → 1H entry — threads.com/@smcandict](https://www.threads.com/@smcandict/post/DAWUyiQC-W6?hl=en)
- [CRT timeframes — tradingfinder.com](https://tradingfinder.com/education/forex/ict-candle-range-theory/)
- [Mastering CRT — scribd.com](https://www.scribd.com/document/898327293/Crt)
