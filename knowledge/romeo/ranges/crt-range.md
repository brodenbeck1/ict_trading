---
name: crt-range
aliases: [CRT, range candle, CRT candle]
category: ranges
related: [candle-range-principle, purge, inside-bars-accumulation, fractal-timeframe-pairing, quality-protocols]
ict_refs: [dealing-range, power-of-three]
parameters:
  range_timeframes: [D, 4H, 1H]
  state: "open -> purged_high|purged_low -> delivered|failed"
detection: not-implemented
---

# The CRT Range

The unit of the whole methodology: a chosen higher-timeframe candle treated as a
dealing range. Its high and low are the liquidity pools; its 50% is equilibrium; the
candles that form inside it (on the same or lower timeframe) are the accumulation;
and the resolution comes when one side is **purged**.

Lifecycle of a CRT:

1. **Range candle closes** — its high/low/50% become the live reference levels.
2. **Accumulation** — subsequent candles hold inside the range
   (see [inside-bars-accumulation](inside-bars-accumulation.md)); liquidity builds on
   both sides.
3. **Purge** — one side is wicked and rejected ([purge](purge.md)); bias is now set
   toward the opposite side.
4. **Delivery** — price crosses the range: first objective the 50%, then the opposing
   extreme, then beyond.

Not every candle is worth treating as a CRT — selection is governed by the
[quality protocols](../protocols/quality-protocols.md) (timing of the candle open,
inside bars, key-level coupling).

## Detection Rules

- Candidate range candle: configurable predicate (default: any D/4H/1H candle whose
  open time matches the timing protocol).
- Maintain state per active CRT: `{high, low, mid, open_time, tf, inside_bar_count,
  purged_side, purge_time, delivered_to_mid, delivered_to_opposite}`.
- A CRT expires unresolved if N subsequent range-tf candles close without a purge
  (config, e.g., N=3), or when superseded by a newer qualified CRT.

## Sources

- [CRT explained — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
- [CRT range & liquidity — tradingfinder.com](https://tradingfinder.com/education/forex/ict-candle-range-theory/)
- [Choosing the best CRT candle — rattibha.com](https://en.rattibha.com/thread/1790141530461622525)
