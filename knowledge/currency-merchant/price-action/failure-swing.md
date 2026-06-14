---
name: failure-swing
aliases: [FS, HPFS, high-probability failure swing, failure string]
category: price-action
related: [draw-on-liquidity, pa-flow, imbalances-to-liquidity, liquidity-sweep-stop-hunt]
ict_refs: [liquidity-sweep-stop-hunt, buy-side-liquidity, sell-side-liquidity]
source_coverage: partial-public
parameters:
  scan_forward_bars: 6        # max bars after LTC to find the HPFS candle
  untested_confirmation: 20   # bars forward the level must remain untested to confirm
detection: not-implemented
---

# Failure Swing (FS) and High Probability Failure Swing (HPFS)

A **failure swing** is any candle high (or low) that has not been taken by a
subsequent candle — untested liquidity resting above (or below) current price.
In a consecutive price leg, every candle either takes the prior candle's extreme
or has its own extreme taken; the one candle in the sequence whose extreme has
*not* been touched is the failure swing.

A **High Probability Failure Swing (HPFS)** is a specific subset that forms
immediately after a confirmed liquidity sweep. It is high probability because:
1. The sweep that preceded it confirms order flow in the opposite direction
2. The HPFS level sits inside the body of the sweeping candle — the zone where
   smart money was active
3. Stops accumulate above (bearish HPFS) or below (bullish HPFS) the untested
   extreme, making it a prime raid target

---

## Detection Rules

### Step 1 — Identify the Liquidity-Taking Candle (LTC)

**Bearish LTC**: a candle whose high exceeds the prior candle's high (sweeps buy
stops above) but whose close falls back below that prior high (rejection).

- `high[i] > high[i-1]`  ← takes prior high (sweeps buy-side liquidity)
- `close[i] < high[i-1]` ← closes back below the swept level (rejection confirmed)

**Bullish LTC**: mirror — low sweeps below the prior candle's low, close recovers
above it.

The swept level does not have to be a raw candle high/low. It can be any named
liquidity pool: a prior HPFS level, a session high/low, an equal-highs cluster,
etc. The rule is the same regardless of the source of liquidity.

### Step 2 — Find the HPFS Candle

After the LTC, scan forward candle by candle. The **first candle** whose:

- **Bearish HPFS**: `high[j] < open[i]` — high is inside the LTC body (below LTC open)
- **Bullish HPFS**: `low[j] > open[i]`  — low is inside the LTC body (above LTC open)

That candle's high (bearish) or low (bullish) = the **HPFS level**.

There may be 1–2 candles between the LTC and the HPFS candle whose extremes are
still above the LTC open; skip those and continue scanning until the condition
is met.

### Validity

- The HPFS level must remain untested (no subsequent candle takes it) to stay
  active. Once taken, it is consumed and the process restarts (see Recursive
  Property below).
- Invalidation: any candle closes beyond the HPFS level in the direction of the
  original sweep (e.g., closes above the HPFS high for a bearish setup) → the
  sweep has failed to produce a reversal; the HPFS is no longer valid.

---

## Recursive Property

A HPFS level is itself a liquidity pool. When price returns and sweeps the HPFS
level (using that as the next LTC), the identical process restarts:

1. HPFS level exists as resting liquidity
2. A new LTC sweeps through that HPFS level and closes back (rejection)
3. First subsequent candle with extreme inside the new LTC body = new HPFS

This means HPFS levels chain in a trending move, each one forming after the
prior is taken. In a sustained down leg you will see stair-stepping HPFS highs,
each sitting progressively lower, each created by the raid of the prior one.

The source of the swept liquidity is irrelevant to the formation logic — raw
candle extremes, prior HPFS levels, session highs/lows, and named pools all
trigger the same HPFS formation sequence when swept and rejected.

---

## Relationship to Draw on Liquidity

HPFS levels are a valid source of DOL (see [[draw-on-liquidity]]). In Kishane's
framework a high counts as buy-side liquidity only if it did **not** already
take a previous high (the "failure strings excluded" pool validity rule). A HPFS
high fits this — it is a high that formed without sweeping above a prior high,
making it untouched buy-side that the algorithm is likely to deliver price toward.

---

## Detection Rules (Implementation Notes)

```
bearish_ltc(i):
    high[i] > high[i-1]       # swept buy-side
    close[i] < high[i-1]      # rejected back below

bearish_hpfs(i, scan_forward=6):
    for j in range(i+1, i+1+scan_forward):
        if high[j] < open[i]:
            return j, high[j]   # first candle inside LTC body = HPFS
    return None

hpfs_valid(j, untested_bars=20):
    max(high[j+1 : j+1+untested_bars]) < high[j]
```

Mirror for bullish (swap high↔low, invert comparisons).

---

## Sources

- User observation / chart annotation — session 2026-06-14
- Consistent with Kishane's "failure strings excluded" pool validity rule in
  draw-on-liquidity.md (see Section 2, Pool validity rule)
