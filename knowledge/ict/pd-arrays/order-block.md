---
name: order-block
aliases: [OB, bullish order block, bearish order block]
category: pd-arrays
related: [breaker-block, mitigation-block, displacement, fair-value-gap, change-in-state-of-delivery]
parameters:
  zone_definition: "open-to-close body of the OB candle; mean threshold = 50% of body"
  liquidity_sweep: "OB candle body (close) must breach a prior swing level — wick-only sweeps do not qualify"
  validation_candle: "a subsequent candle must close above (bullish OB) or below (bearish OB) the OB candle's body"
detection: implemented
---

# Order Block (OB)

The **last opposing candle before a displacement** that also sweeps liquidity with its
body — e.g., the last down-closed candle before an aggressive rally, where the body
close breaks a prior swing low. ICT's narrative: institutions used that candle to
accumulate (sweep weak longs for inventory), then drove price away; a return to it
re-offers the institutional price.

## Required Conditions

### 1 — Liquidity sweep in the body

The OB candle's **body close** (not just the wick) must breach a prior swing
high (bearish OB) or swing low (bullish OB). A wick-only sweep does not qualify — the
body must transact through the level, showing institutional commitment.

- **Bullish OB**: bearish candle (close < open) whose **close** goes below a prior swing
  low, sweeping sell-side liquidity with the body.
- **Bearish OB**: bullish candle (close > open) whose **close** goes above a prior swing
  high, sweeping buy-side liquidity with the body.

### 2 — Validation candle

After the liquidity-taking OB candle, a subsequent candle must **close back through**
the OB candle to validate the reversal:

- **Bullish OB validated**: a subsequent candle closes **above** the OB candle (above
  its open, the top of the body). This confirms the sweep was a reversal, not
  continuation.
- **Bearish OB validated**: a subsequent candle closes **below** the OB candle (below
  its open, the bottom of the body).

Until the validation candle prints, the candle is only a *candidate* OB. If price
continues in the sweep direction instead, it is not an OB.

## Zone and States

- **Zone**: `(close, open)` for bullish OB (body of the bearish sweep candle);
  `(open, close)` for bearish OB. Mean threshold = 50% of the body.
- **States**: `candidate → validated → tested → broken`
  - Broken = subsequent close through the far side of the zone →
    candidate [breaker-block](breaker-block.md).

## Additional Filters (2020 forex notes)

- Retracement objectives *into* the block: ① proximal edge, ② the candle open,
  ③ midpoint. A retracement **through 50%** weakens the block; fall back to the prior OB.
- When an OB is broken, the previous OB in the same leg becomes the candidate.
- After an SMT divergence, prefer the *second* block formed in the new direction.
- A nearby swing high/low can turn price before it precisely tags the block.
- Distinguish from the FVG: the OB is where the move *originated*; the FVG is the
  inefficiency the move *left behind* — together they bracket the entry region.

## Detection Rules

- Candidate: bearish (bullish) candle whose body close breaches a prior swing low
  (high) — the liquidity-sweep-in-body condition.
- Validated: confirmed once a subsequent candle closes above (below) the OB candle.
- Zone: body `(close, open)` for bullish; `(open, close)` for bearish.
  Mean threshold = zone midpoint.
- Entry convention: limit at proximal edge or mean threshold; stop beyond OB extreme.

## Sources

- [ICT order block explained — innercircletrader.net](https://innercircletrader.net/tutorials/ict-order-block/)
- [Order blocks, breakers, mitigation — theicttrader.com](https://theicttrader.com/2024/03/24/order-blocks-breaker-blocks-and-mitigation-blocks/)
- [Key ICT concepts — tradezella.com](https://www.tradezella.com/learning-items/key-ict-concepts)
- Selection rules: `strategies/notes/ict-forex-notes-mmari-2020.md` §7 (2020 forex-era ICT)
