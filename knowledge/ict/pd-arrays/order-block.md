---
name: order-block
aliases: [OB, bullish order block, bearish order block]
category: pd-arrays
related: [breaker-block, mitigation-block, displacement, fair-value-gap, change-in-state-of-delivery]
parameters:
  zone_definition: "body vs full candle range — config flag (ICT later teaching favors open-to-close body; mean threshold = 50% of the OB)"
  validation: "must be followed by displacement that breaks structure / leaves an FVG"
detection: not-implemented
---

# Order Block (OB)

The **last opposing candle (or candle series) before a displacement move** — e.g., the
last down-closed candle before an aggressive rally. ICT's narrative: that candle is
where institutions accumulated their position (their orders are "blocked" there), so a
return to it re-offers the institutional price.

- **Bullish OB**: last down-closed candle before an up-displacement that breaks
  structure. Zone of interest for longs on the retest.
- **Bearish OB**: last up-closed candle before a down-displacement.

A candle is *not* an order block just for being the last opposite color — the
subsequent move must show sponsorship (displacement, structure break, ideally an FVG).
The OB's **mean threshold** (50% of the candle) is the defended midpoint; deep tests
beyond it weaken the block. Distinguish from the FVG: the OB is where the move
*originated*; the FVG is the inefficiency the move *left behind* — together they bracket
the entry region.

## Detection Rules

- Candidate: candle (or consecutive same-color candles) of color opposite to the
  following leg, immediately preceding a displacement that breaks a swing or leaves
  an FVG.
- Zone: `(open, close)` of the candle (body convention) or `(low, high)` (full range) —
  config flag; mean threshold = zone midpoint.
- States: `fresh → tested → broken` (close through the far side → candidate
  [breaker-block](breaker-block.md)).
- Entry convention: limit at zone edge or mean threshold; stop beyond the OB extreme.

## Sources

- [ICT order block explained — innercircletrader.net](https://innercircletrader.net/tutorials/ict-order-block/)
- [Order blocks, breakers, mitigation — theicttrader.com](https://theicttrader.com/2024/03/24/order-blocks-breaker-blocks-and-mitigation-blocks/)
- [Key ICT concepts — tradezella.com](https://www.tradezella.com/learning-items/key-ict-concepts)
