---
name: market-maker-models
aliases: [MMXM, MMBM, MMSM, market maker buy model, market maker sell model]
category: models
related: [power-of-three, smt-divergence, market-structure-shift, change-in-state-of-delivery, dealing-range]
parameters:
  phases: [original consolidation, engineering liquidity (curve left side), smart money reversal, redelivery (curve right side)]
detection: not-implemented
---

# Market Maker Buy / Sell Models (MMXM)

The **whole-day/whole-leg map** of which the other models are fragments: a symmetric
"V" (buy model) or "Λ" (sell model) shaped delivery curve.

**Market Maker Sell Model (MMSM)** anatomy:
1. **Original consolidation** — the range where the story starts;
2. **Left side / engineering** — price rallies *away* from consolidation in
   accumulation legs, building sell-side fuel beneath each higher low and inducing
   longs;
3. **Smart money reversal (SMR)** — at a higher-timeframe premium array, price sweeps
   the final buy-side pool; confirmation stack: SMT divergence, MSS/CISD, displacement
   FVG;
4. **Right side / distribution** — price redelivers *down through the same levels*,
   targeting the liquidity engineered on the left side, back to (and often through)
   the original consolidation.

MMBM is the mirror. Practical power: the left side tells you the **target ladder** for
the right side — each left-side consolidation/low is a right-side objective. The SMR
is where reversal models (turtle soup, unicorn) fire; the right side is where
continuation entries (mitigation blocks, OTE) stack.

**Early 6-phase enumeration (2020 forex-era buy model)**: ① consolidation at HTF
resistance/bearish OB → ② run to support (break + retest of the consolidation) →
③ smart money reversal (buy OTE at key support) → ④ accumulation (low-risk buys) →
⑤ re-accumulation at/near the prior accumulation → ⑥ distribution after the stops
above it are taken. The **re-accumulation stage is the continuation/reversal tell**:
HTF-bearish ⇒ price respects the *low* of the prior accumulation and rolls over;
HTF-bullish ⇒ price trades above it, stopping out counter-trend shorts. Phases ①/③/⑥
are the actionable zones.

## Detection Rules

- Hard to detect prospectively in full; decompose: consolidation detection (range
  compression), leg counting away from it, then SMR = sweep + MSS at/beyond a HTF
  array.
- Right-side trade management: targets = left-side swing lows/consolidation mids in
  sequence.
- Research label (retrospective): days/legs matching "out-and-back to consolidation"
  symmetry, for measuring how often the full curve completes.

## Sources

- [Market maker buy model — innercircletrader.net](https://innercircletrader.net/tutorials/ict-market-maker-buy-model/)
- [Market maker sell model — innercircletrader.net](https://innercircletrader.net/tutorials/ict-market-maker-sell-model/)
- [MMXM overview — michaeljhuddleston.org](https://michaeljhuddleston.org/notes/ict-market-maker-model-mmxm-trade-with-smart-money-not-against-it/)
- [MMXM components — tradingview.com](https://www.tradingview.com/script/4eQPT3aC-MMXM-ICT-TradingFinder-Market-Maker-Model-PO3-CHoCH-CSID-FVG/)
- 6-phase early version + re-accumulation tell: `strategies/notes/ict-forex-notes-mmari-2020.md` §11
