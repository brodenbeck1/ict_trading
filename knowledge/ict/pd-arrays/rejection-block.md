---
name: rejection-block
aliases: [RB]
category: pd-arrays
related: [order-block, breaker-block, liquidity-sweep-stop-hunt]
parameters:
  wick_dominance: "wick length vs body — long-wick candle at a swing extreme that swept liquidity"
detection: not-implemented
---

# Rejection Block

The **wick** of a long-tailed candle that swept liquidity at a swing extreme — the wick
itself becomes the reversal zone. Where the order block trades off the candle *body*,
the rejection block trades off the *wick*: the territory price explored and was
violently rejected from.

Bearish rejection block: at a swing high, a candle (or pair of candles) spikes above
the prior high (taking buy stops) and closes well off the top, leaving a long upper
wick. The zone from the **top of the body to the top of the wick** is the rejection
block; price returning into that wick zone offers the short, anticipating the same
sellers defend it. Mirror with lower wicks at swept lows.

## Detection Rules

- Candidate: candle at a confirmed swing extreme whose wick (in the sweep direction)
  >= k × body (e.g., k = 1.5) AND whose extreme violated a prior liquidity pool.
- Bearish zone = `(max(open, close), high)` of the candle; bullish =
  `(low, min(open, close))`.
- Entry: retrace into the wick zone after the swing is confirmed; stop beyond the wick
  extreme.
- Invalidation: close beyond the wick extreme (the rejection failed → likely
  continuation/run).

## Sources

- [ICT rejection block — innercircletrader.net](https://innercircletrader.net/tutorials/ict-rejection-block/)
- [PD arrays overview — fxopen.com](https://fxopen.com/blog/en/what-is-a-pd-array-in-ict-and-how-can-you-use-it-in-trading/)
