---
name: consequent-encroachment
aliases: [CE, 50% of gap]
category: pd-arrays
related: [fair-value-gap, nwog-ndog, premium-discount]
parameters:
  level: "0.5 of the gap/wick height"
detection: not-implemented
---

# Consequent Encroachment (CE)

The **50% level of a gap or wick** — ICT's term for the midpoint of an FVG, NWOG/NDOG,
or a large wick. It is frequently the most reactive single line inside the zone:

- Strong setups often fill an FVG only **to CE** before continuing — so an aggressive
  entry sits at the gap edge, a conservative one at CE.
- For NWOG/NDOG, CE is the institutional reference line price respects even after the
  gap itself has been traded through.
- For a long wick (e.g., rejection block), the wick's CE acts as the support/resistance
  midpoint on retests.

The same "midpoint matters" logic appears at every scale: equilibrium of a dealing
range, mean threshold of an order block, CE of a gap — all are 50% lines of a defined
object.

## Detection Rules

- `ce = (zone_high + zone_low) / 2` for any registered gap/wick object.
- Feature events: `touched_ce`, `respected_ce` (reversed within k bars of touching),
  `closed_through_ce` (weakens the zone; full fill likely).
- Entry refinement rule (config): place limit at CE instead of zone edge when the zone
  height > x points (wide gaps rarely fill edge-to-edge before reacting).

## Sources

- [NDOG & consequent encroachment — innercircletrader.net](https://innercircletrader.net/tutorials/ict-new-day-opening-gap-ndog/)
- [NDOG / CE calculation — tradingfinder.com](https://tradingfinder.com/education/forex/ict-new-day-opening-gap/)
