---
name: unicorn
aliases: [unicorn model, breaker + FVG]
category: models
related: [breaker-block, fair-value-gap, liquidity-sweep-stop-hunt, market-structure-shift]
parameters:
  required_overlap: "FVG zone must intersect the breaker block zone — adjacency does not count"
  causality: "breaker forms first (post-sweep); FVG forms during/after the displacement through it"
detection: not-implemented
---

# Unicorn Model

The high-precision confluence model: a **breaker block and a fair value gap occupying
the same price range**. Formation (bullish):

1. Swing low → swing high → **sweep below the swing low** (mandatory raid);
2. Displacement up **through the swing high** (MSS) — this break converts the last
   down-candle(s) into a [breaker block](../pd-arrays/breaker-block.md);
3. The displacement leg leaves an **FVG that overlaps the breaker**;
4. **Entry zone = the intersection** of breaker and FVG; limit there on the retrace.
   Stop below the sweep low (or below the overlap zone); targets per the standard
   liquidity logic.

Hard rules: no sweep → no breaker → no Unicorn; FVG merely *near* the breaker doesn't
qualify — the zones must intersect. The overlap concentrates two independent reasons
for the algorithm to defend the price, which is the model's whole edge claim.

## Detection Rules

- Run breaker detection; for each new breaker, query FVGs created by the breaking
  displacement; require `intersection(breaker_zone, fvg_zone) != empty`.
- Entry zone = the intersection; entry at zone edge or its CE (config).
- Validity window: first retrace only; invalidate on close through the far side of
  the overlap zone.
- Confluence bonuses for scoring: SMT at the sweep, killzone timing, HTF PD array
  context.

## Sources

- [ICT unicorn model — innercircletrader.net](https://innercircletrader.net/tutorials/ict-unicorn-model/)
- [Unicorn setup rules — arongroups.co](https://arongroups.co/technical-analyze/ict-unicorn-model/)
- [Unicorn strategy — luxalgo.com](https://www.luxalgo.com/blog/ict-unicorn-model-strategy-how-to-use/)
- [Unicorn identification — fluxcharts.com](https://www.fluxcharts.com/articles/trading-strategies/ict-strategies/ict-unicorn)
