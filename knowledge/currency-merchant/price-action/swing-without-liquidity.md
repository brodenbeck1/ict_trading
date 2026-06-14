---
name: swing-without-liquidity
aliases: [no liquidity swing, distributed swing, failure string]
category: price-action
related: [failure-swing, draw-on-liquidity, pool_validity]
source_coverage: partial-public
parameters: {}
detection: implemented
---

# Swing High/Low Without Liquidity

A swing high or low that **already took out a prior swing of equal or greater magnitude**.
Because the liquidity at that level has already been distributed (the stops above or below
it have already been run), there are no meaningful resting orders remaining there.

It does **not** qualify as a DOL candidate. Price returning to that level has no
accumulation of stops to fuel a move — the level is effectively empty.

## Definition

**Swing high without liquidity (bullish context)**:
- `high[i] > high[i-1]` — this high already swept the prior swing high
- The liquidity above the prior high was consumed when this candle printed

**Swing low without liquidity (bearish context)**:
- `low[i] < low[i-1]` — this low already swept the prior swing low

**Exception**: equal prices (`high[i] == high[i-1]`) do NOT disqualify — relative equal
highs/lows represent a pool where liquidity has doubled up, not been consumed.

## Relationship to HPFS

The complement of this concept is the [[failure-swing]] (HPFS) — a swing whose extreme
has **not** been taken. Where a swing without liquidity has been fully distributed, an
HPFS still has resting orders above (bearish) or below (bullish) it and qualifies as a
DOL candidate.

| Classification | Prior swing taken? | Resting liquidity? | DOL candidate? |
|---|---|---|---|
| HPFS (failure swing) | No | Yes | Yes |
| Swing without liquidity | Yes | No | No |

## Detection

Implemented in `src/ict/concepts/pool_validity.py` → `classify_swing_liquidity(swing_points, swing_type)`.
Takes `swing_highs` or `swing_lows` from `SwingPointScanner` and returns the
same DataFrame with a `'classification'` column: `'failure_swing'` or `'no_liquidity'`.
