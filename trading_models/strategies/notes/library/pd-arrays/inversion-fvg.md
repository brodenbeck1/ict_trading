---
name: inversion-fvg
aliases: [IFVG, inverse fair value gap, inversion fair value gap]
category: pd-arrays
related: [fair-value-gap, breaker-block, market-structure-shift]
parameters:
  inversion_rule: "candle CLOSE fully beyond the far edge of the FVG (wick-through is not inversion)"
detection: not-implemented
---

# Inversion Fair Value Gap (IFVG)

A **failed FVG that flips polarity**. When price closes through a fair value gap in the
direction opposite its original delivery, the gap stops acting as its old self and
becomes a zone of the opposite kind:

- A bullish FVG that price closes **below** → becomes bearish resistance (sellers
  defend the broken gap on the retest).
- A bearish FVG that price closes **above** → becomes bullish support.

Logic parallels the breaker block (failed order block → flipped polarity), at the
gap level. IFVGs are favored as confirmation in reversal trades: after a sweep, the
*inversion* of a nearby FVG is itself evidence of the new delivery direction, and the
retest of the inverted gap is the entry.

## Detection Rules

- Given a tracked FVG, inversion event when a candle **closes** fully beyond the far
  edge (bullish FVG: `close < zone_low`; bearish: `close > zone_high`).
- After inversion, re-register the zone with flipped side; entry = first retrace into
  the inverted zone, stop beyond its far edge.
- Confidence features: displacement on the inverting candle, inversion coinciding with
  an MSS, gap freshness before inversion.

## Sources

- [ICT inversion FVG — innercircletrader.net](https://innercircletrader.net/tutorials/ict-inversion-fair-value-gap/)
- [Inverse FVG concept — fxopen.com](https://fxopen.com/blog/en/what-is-an-inverse-fair-value-gap-ifvg-concept-in-trading/)
- [IFVG explained — fluxcharts.com](https://www.fluxcharts.com/articles/inversion-fair-value-gaps-ifvg-explained)
