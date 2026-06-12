---
name: fractal-timeframe-pairing
aliases: [timeframe alignment, HTF range LTF entry, fractality]
category: core
related: [candle-range-principle, crt-range, entry-triggers]
ict_refs: [entry-sequence]
parameters:
  standard_pairs: "Daily CRT -> 1H entry; 4H CRT -> 15m entry; 1H CRT -> 5m/1m entry"
detection: not-implemented
---

# Fractal Timeframe Pairing

CRT is explicitly fractal: the same range-purge-deliver behavior appears on every
timeframe, so the methodology is organized as **HTF range / LTF execution** pairs:

| CRT (range) timeframe | Entry (execution) timeframe |
|---|---|
| Weekly / Daily | 1H |
| 4H (the workhorse) | 15m |
| 1H | 5m or 1m |

The HTF candle supplies the range, the bias (which side got purged), and the targets
(opposing 50%, opposing extreme). The LTF supplies the confirmation (MSS/CISD after
the purge) and the precise entry. Daily, 4H, and 1H are taught as the cleanest range
timeframes; below 1H the ranges get noisy.

Nesting also stacks: a 15m entry setup inside a 4H purge inside a daily-range
discount is the highest-grade alignment — each layer is the same pattern at a
different scale.

## Detection Rules

- Implement CRT detection generically over the normalized candle-range object, then
  instantiate with `(range_tf, entry_tf)` config pairs.
- Resampling note for this project's UTC 1m data: 4H candles must be **anchored to NY
  session opens** (1am/5am/9am NY), not the default 00:00-UTC grid — use an anchor
  offset when resampling (EDT: 05:00 UTC ⇒ `offset='1h'` on the 4H grid; recompute
  per DST regime).
- Confluence score: count of nested aligned layers (entry-tf setup within range-tf
  purge within higher-range context).

## Sources

- [CRT timeframes — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
- [Daily CRT→1H, 4H CRT→15m — threads.com/@smcandict](https://www.threads.com/@smcandict/post/DAWUyiQC-W6?hl=en)
- [CRT complete guide — tradingfinder.com](https://tradingfinder.com/education/forex/ict-candle-range-theory/)
