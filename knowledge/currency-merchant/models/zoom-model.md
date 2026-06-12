---
name: zoom-model
aliases: [zoom, consolidation stophunt model]
category: models
related: [pa-flow, cycle-order-flow, rules-of-engagement]
ict_refs: [power-of-three, liquidity-sweep-stop-hunt, inducement, turtle-soup]
source_coverage: sparse-public   # named in the curriculum ("Understanding consolidations and stophunts — Zoom model"); details paywalled
parameters: {}
detection: not-implemented
---

# The Zoom Model (Consolidations & Stop Hunts)

CM Academy's framework for **consolidation conditions**: per the curriculum outline,
the Zoom model is how Kishane teaches "understanding consolidations and stophunts" —
reading a ranging market's engineered liquidity and the stop hunt that resolves it,
rather than getting chopped trading the range's interior.

From the public outline and how it slots into his system, the model's job is to
answer: which side of the consolidation is being engineered for the raid, and when
(by cycle time) is the raid due? The expected anatomy is the familiar one —
consolidation builds double-sided liquidity; the algorithm purges the weaker side at
a key time (cycle boundary / session open); delivery then expands away from the purge
— i.e., the PO3/turtle-soup engine with CM's time grid attached.

**Details are paywalled** — the name "Zoom" itself (what is zoomed, LTF drill-down or
range magnification) is not publicly documented. Populate this file properly from his
videos via `/strategy-from-transcript`; until then, treat the detection sketch below
as the ICT-equivalent scaffold.

## Detection Rules (provisional scaffold)

- Consolidation detector from the PA-flow classifier (range compression).
- Liquidity map of the range: equal highs/lows, range extremes, embedded voids.
- Raid watch at key times: purge of one extreme + close back inside (CRT/turtle-soup
  detectors) during a cycle-boundary window → bias = opposite extreme.
- Defer entry mechanics to the Rules of Engagement (raided OB candidate forms at the
  purge).

## Sources

- [CM Academy outline ("Zoom model") — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
