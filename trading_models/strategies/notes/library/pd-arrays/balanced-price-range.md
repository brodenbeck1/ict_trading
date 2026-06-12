---
name: balanced-price-range
aliases: [BPR]
category: pd-arrays
related: [fair-value-gap, displacement, liquidity-sweep-stop-hunt]
parameters:
  overlap_rule: "zone = price intersection of a bullish FVG and a bearish FVG from opposing displacements"
detection: not-implemented
---

# Balanced Price Range (BPR)

The **overlap of two opposing fair value gaps**: a displacement in one direction leaves
an FVG, then a displacement back the other way leaves an opposite FVG through the same
prices. The overlapping slice has now been delivered efficiently *both ways* — it is
"balanced" — and the zone becomes a sharp reaction level for the direction of the
*second* displacement.

Typical context: a stop hunt creates the first (false-move) FVG; the reversal
displacement creates the second. The BPR marks where the algorithm flipped, and a
retest of it is a high-precision entry consistent with the new direction.

## Detection Rules

- Find a bullish FVG `B` and bearish FVG `S` whose zones intersect and whose creating
  legs are opposite-direction displacements within a window of N bars (e.g., N <= 60
  on 1-5m).
- BPR zone = `(max(B.low_edge, S.low_edge), min(B.high_edge, S.high_edge))`.
- Direction = direction of the *later* FVG's displacement; entry on first retrace into
  the BPR; stop beyond the far side of the zone.
- Invalidation: candle close fully through the BPR against its direction.

## Sources

- [FVG family (BPR) — innercircletrader.net](https://innercircletrader.net/tutorials/fair-value-gap-trading-strategy/)
- [Inverse FVG & related zones — fxopen.com](https://fxopen.com/blog/en/what-is-an-inverse-fair-value-gap-ifvg-concept-in-trading/)
