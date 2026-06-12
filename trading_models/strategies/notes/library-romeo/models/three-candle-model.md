---
name: three-candle-model
aliases: [AMD candles, CRT turtle soup, the soup, 3-candle CRT]
category: models
related: [crt-range, purge, entry-triggers, targets, stops-invalidation]
ict_refs: [power-of-three, turtle-soup, judas-swing]
parameters:
  candle_1: "accumulation — forms the range"
  candle_2: "manipulation — 'the soup': wicks beyond candle 1's extreme, closes back inside"
  candle_3: "distribution — delivers through the range to the opposite side"
detection: not-implemented
---

# The Three-Candle Model (A-M-D)

CRT's canonical pattern, the Power of Three written in exactly three range-timeframe
candles:

1. **Candle 1 — Accumulation**: forms the range; its high/low are the liquidity.
2. **Candle 2 — Manipulation ("the soup")**: wicks beyond one extreme of candle 1
   (taking the stops — the turtle-soup event) and **closes back inside** candle 1's
   range. This candle's wick is the purge; its body close inside is the tell.
3. **Candle 3 — Distribution**: opens, and delivers through the range toward (and
   typically through) candle 1's opposite extreme. Per the source material: the
   entries here are the quickest and highest-probability.

Entry mechanics: trigger on the LTF after candle 2's purge (CISD/MSS per
[entry-triggers](../entries/entry-triggers.md)), or at candle 3's open / the 50% of
candle 2 on the retrace. Stop beyond candle 2's wick; targets per the standard
[ladder](../entries/targets.md) (candle 1 mid → opposite extreme → beyond).

On 4H with the [timing protocol](../protocols/timing-protocol.md), this is the
1 AM (accumulation) → 5 AM (manipulation) → 9 AM (distribution) day shape — the CRT
version of London-Judas-then-NY-delivery.

## Detection Rules

- Pattern over consecutive range-tf candles (bullish):
  `low[2] < low[1] and close[2] > low[1]` (soup), then entry conditions on candle 3:
  long while `price < mid(candle_1)` with confirmation.
- Strict variant adds: `high[2] <= high[1]` (candle 2 purges only one side) and
  candle 2 close within candle 1's **body** (stronger rejection).
- Label completed patterns by outcome (reached mid / opposite / failed) for the
  protocol-ablation research.

## Sources

- [CRT AMD phases — mql5.com](https://www.mql5.com/en/articles/20323)
- [CRT & turtle soup — scribd.com](https://www.scribd.com/document/846803727/Basic-of-CRT)
- [CRT three stages — coconote.app](https://coconote.app/notes/faf87347-ff5f-46ba-b200-ffd1cd87e785)
- [CRT trades indicator (TS, AMD, inside bars) — tradingview.com](https://www.tradingview.com/script/lEJTsZZ2-CRT-Trades-turtle-soup-A-M-D-ranges-with-inside-bars/)
