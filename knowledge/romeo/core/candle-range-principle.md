---
name: candle-range-principle
aliases: [every candle is a range, candle anatomy, CRT principle]
category: core
related: [fractal-timeframe-pairing, crt-range, wick-ce]
ict_refs: [power-of-three, dealing-range]
parameters: {}
detection: not-implemented
---

# The Candle Range Principle

The axiom underneath all of Candle Range Theory: **every single candle is a range** —
not a data point but a complete liquidity story. A candle's high and low are the
range extremes (liquidity pools beyond each), its open/close mark how the range was
delivered, and its wicks record where price was rejected.

Consequences:

- A higher-timeframe candle *is* a dealing range on the lower timeframe: the 4H
  candle's high/low are the range a 15m trader operates inside.
- Every candle plays out its own Power of Three — open (accumulation), wick against
  the close direction (manipulation), body expansion (distribution). The OHLC/OLHC
  sequencing of the ICT framework is the same observation
  (see ICT library: [ohlc-candle-profiles](../../ict/daily-bias/ohlc-candle-profiles.md)).
- Candle levels — high, low, open, close, body midpoint, wick midpoints — are all
  tradable reference levels, not just the swing extremes.

This reframing is why CRT needs so few concepts: range, purge, and time replace most
of the ICT pattern zoo.

## Detection Rules

- Represent any candle as
  `{open, high, low, close, body: (min(o,c), max(o,c)), upper_wick, lower_wick, mid: (h+l)/2}`.
- Derived levels per candle: range 50%, body 50%, wick CEs (see [wick-ce](../ranges/wick-ce.md)).
- All downstream CRT detection consumes this normalized candle-range object at any
  timeframe.

## Sources

- [CRT explained — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
- [CRT guide — writofinance.com](https://www.writofinance.com/candle-range-theory-crt/)
- [CRT key levels & setups — grandalgo.com](https://grandalgo.com/blog/candle-range-theory-crt-explained)
