---
name: inside-bars-accumulation
aliases: [inside bars, IB protocol, accumulation candles]
category: ranges
related: [crt-range, purge, quality-protocols]
ict_refs: [power-of-three, inducement]
parameters:
  inside_bar_rule: "candle i is inside the CRT if high[i] <= crt.high and low[i] >= crt.low"
  quality: "more inside bars before the purge = higher probability"
detection: not-implemented
---

# Inside Bars (Accumulation)

Candles that form **entirely within the CRT range** after it closes. Each inside bar
is a session of two-way trade that adds resting orders on both sides of the range —
stops above the high, stops below the low — without resolving it. CRT doctrine:
**the more inside bars, the higher the probability** that the eventual purge produces
a significant delivery, because more liquidity has accumulated to fuel it.

Inside bars are the accumulation phase of the range's Power of Three; the purge that
ends them is the manipulation. A refinement from the source material: after a long
inside-bar sequence, wait for a lower-timeframe **CISD/CSD** at the purge rather than
entering on the wick alone — the extra step filters genuine reversals from
continuation breaks.

## Detection Rules

- Count consecutive range-tf candles satisfying the inside-bar rule after the CRT
  candle closes; store `inside_bar_count` on the CRT state.
- Feature: `accumulation_span = inside_bar_count * tf_minutes` (time-based liquidity
  proxy).
- Quality tiers (tunable): 0 IBs = base; 1–2 = improved; 3+ = high-grade compression.
- Research metric: post-purge delivery distance (in range heights) as a function of
  `inside_bar_count`, per instrument.

## Sources

- [Mastering CRT (inside bars protocol) — scribd.com](https://www.scribd.com/document/898327293/Crt)
- [CRT trades with inside bars — tradingview.com](https://www.tradingview.com/script/lEJTsZZ2-CRT-Trades-turtle-soup-A-M-D-ranges-with-inside-bars/)
- [CRT study guide — studylib.net](https://studylib.net/doc/27924459/candle-range-theory)
