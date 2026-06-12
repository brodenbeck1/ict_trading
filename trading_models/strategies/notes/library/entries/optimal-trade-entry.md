---
name: optimal-trade-entry
aliases: [OTE, 70.5 level, fib entry]
category: entries
related: [premium-discount, entry-sequence, fair-value-gap, one-shot-one-kill]
parameters:
  zone: [0.62, 0.79]
  sweet_spot: 0.705
  fib_anchor: "body-to-body (open/close) of the impulse leg, per ICT convention; wick-to-wick is the common alternative — config flag"
detection: not-implemented
---

# Optimal Trade Entry (OTE)

The Fibonacci retracement zone **between 62% and 79%** of an impulse leg, with
**70.5%** (midpoint of 61.8 and 79) as the sweet spot. After a displacement leg, the
OTE marks the retracement depth that is deep enough to be a genuine discount/premium
but shallow enough that the leg's structure is intact.

Used two ways:
1. **Standalone entry zone** — in trending conditions: impulse leg up → wait for
   retrace into 62–79% → long with stop below the leg's origin.
2. **Confluence grader** — an FVG or order block *inside* the OTE zone of the
   displacement leg is a higher-quality entry than one outside it.

Levels beyond entry: ICT's fib profile adds -0.27 and -0.62 extension as the first two
targets, and symmetrical/2 SD projections for runners.

## Detection Rules

- Anchor the fib on the displacement leg (post-sweep leg in reversal models):
  `low_anchor` to `high_anchor` per `fib_anchor` convention.
- OTE zone for longs: `[high - 0.79 * leg, high - 0.62 * leg]`
  (prices between the 62% and 79% retracement).
- Entry trigger: limit at 0.705, or first touch of the zone with LTF confirmation
  (CHoCH/FVG reaction) — config.
- Invalidation: trade beyond 1.0 (the leg origin) before fill, or retracement closing
  past 0.89 (failed OTE — stand aside).

## Sources

- [ICT OTE pattern — innercircletrader.net](https://innercircletrader.net/tutorials/ict-optimal-trade-entry-ote-pattern/)
- [ICT fib settings (70.5%, std dev) — innercircletrader.net](https://innercircletrader.net/tutorials/ict-fibonacci-levels/)
- [OTE with fibonacci — tradingstrategyguides.com](https://tradingstrategyguides.com/understanding-ict-optimal-trade-entry-ote/)
- [OTE strategy & key levels — tradingfinder.com](https://tradingfinder.com/education/forex/ict-optimal-trade-entry-pattern/)
