---
name: pa-flow
aliases: [price action flow, PA flow, expansion consolidation flow]
category: price-action
related: [voids-in-delivery, imbalances-to-liquidity]
ict_refs: [displacement, power-of-three, internal-external-range-liquidity]
source_coverage: sparse-public
parameters:
  states: [consolidation, expansion, retracement, reversal]
detection: not-implemented
---

# PA Flow (Price Action Flow)

CM Academy's framing of market state: price is always in one of four flow states —
**consolidation, expansion, retracement, reversal** — and every concept in the
curriculum is conditioned on which state is active. The "flow" is the alternation:
consolidation builds liquidity → expansion delivers it → retracement re-prices the
expansion's inefficiencies → either continuation (new expansion) or reversal.

Why it leads the curriculum: entries are taught **for expanding markets**
([type-1-type-2-entries](../models/type-1-type-2-entries.md)) and separately **for
consolidations/stop hunts** ([zoom-model](../models/zoom-model.md)) — using the wrong
playbook for the current state is the diagnosed failure mode. The
[gj-model](../models/gj-model.md) exists specifically to recognize the *prelude* of a
consolidation→expansion transition.

This maps onto ICT vocabulary as: consolidation = accumulation/engineered liquidity;
expansion = displacement; retracement = the return to FVG/OB; reversal = the SMR.

## Detection Rules (provisional)

- State classifier on the working timeframe, e.g.: consolidation = range compression
  (n-bar range < k × ATR); expansion = displacement-leg detector from the ICT
  library; retracement = counter-leg < 79% of the expansion; reversal = full
  retrace + opposing structure break.
- Emit the state sequence as a feature stream; models subscribe and gate their
  entries on required states.
- Validation: state-transition matrix frequencies per session on ES/NQ/YM.

## Sources

- [CM Academy outline ("Understanding the PA flow") — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
