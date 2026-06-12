---
name: 4h-crt-model
aliases: [4H CRT, 1am-5am model, H4 model]
category: models
related: [three-candle-model, timing-protocol, fractal-timeframe-pairing, entry-triggers, quality-protocols]
ict_refs: [killzones, model-2022]
parameters:
  range_candle: "the 1:00 AM NY 4H candle (alt: 5:00 AM, 9:00 PM)"
  purge_candle: "the 5:00 AM NY 4H candle (London)"
  delivery_candle: "the 9:00 AM NY 4H candle (New York)"
  entry_tf: 15m
detection: not-implemented
---

# The 4H CRT Model

The flagship day-trading application — the three-candle model pinned to the clock:

1. **1:00 AM NY 4H candle** closes at 5 AM → its high/low define the day's CRT
   (this candle contains the Asia-late/London-early range).
2. **5:00 AM NY 4H candle** (the London candle) is watched for the **purge** of the
   1 AM range — wick beyond one extreme, close back inside. London doing what London
   does: the manipulation.
3. **9:00 AM NY 4H candle** (the New York candle) is the expected **distribution**
   — entries on the 15m after the purge ride this candle's delivery to the opposite
   side of the 1 AM range and beyond.

Quality stack on top: inside bars between 1 AM close and the purge, the purge landing
on a daily key level, purge occurring inside the London killzone proper, and daily
range context agreeing. For ES/NQ/YM the 9 AM candle contains the 9:30 cash open —
expect the delivery leg to engage around it.

## Detection Rules

- Resample to NY-anchored 4H (see [timing-protocol](../protocols/timing-protocol.md)
  for the UTC offset trap). CRT = the candle opening 01:00 NY.
- Purge window = the 05:00 NY candle (intrabar detection on 15m/1m for earlier
  entries); delivery window = the 09:00 candle, optionally extended to 13:00.
- One setup per day per instrument; skip if double-purge or no purge by 09:00.
- This model is the natural first CRT backtest for the project: fully mechanical,
  one trade/day, maps cleanly onto the existing walk-forward day loop.

## Sources

- [4H CRT (1AM and 5AM) — tradingview.com](https://www.tradingview.com/script/kXR0vkG2-4H-CRT-1AM-and-5AM/)
- [4HR CRT models guide — scribd.com](https://www.scribd.com/document/886606986/Guide-to-4hr-Crt-Models)
- [CRT timing — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
