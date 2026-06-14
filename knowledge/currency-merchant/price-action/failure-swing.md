---
name: failure-swing
aliases: [FS, HPFS, RB HPFS, OB HPFS, high-probability failure swing, rejection block HPFS, order block HPFS, failure string]
category: price-action
related: [draw-on-liquidity, pa-flow, imbalances-to-liquidity, liquidity-sweep-stop-hunt]
ict_refs: [liquidity-sweep-stop-hunt, buy-side-liquidity, sell-side-liquidity, rejection-block, order-block]
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

There are **two variants** depending on whether the LTC takes liquidity with its
wick or its body:

---

## Variant 1 — Rejection Block HPFS (RB HPFS)

The **wick** of the LTC takes liquidity. The candle sweeps the prior high/low but
the **close** falls back on the originating side — a classic rejection / wick sweep.

### Step 1 — Identify the LTC (Rejection Block)

**Bearish RB LTC**: wick sweeps prior high, close rejects back below it.
- `high[i] > high[i-1]`  ← wick takes buy-side (sweeps above prior high)
- `close[i] < high[i-1]` ← close falls back below the swept level

**Bullish RB LTC**: mirror — wick sweeps below prior low, close recovers above.
- `low[i] < low[i-1]`
- `close[i] > low[i-1]`

### Step 2 — Find the HPFS Candle

Scan forward from the LTC. The **first candle** whose extreme is inside the LTC
body (between open and close):

- **Bearish**: `high[j] < open[i]` → HPFS level = `high[j]`
- **Bullish**: `low[j] > open[i]`  → HPFS level = `low[j]`

---

## Variant 2 — Order Block HPFS (OB HPFS)

The **body** of the LTC takes liquidity. The candle's close crosses the prior
high/low — the body (not just a wick) consumed the opposing liquidity, creating
an order block structure.

### Step 1 — Identify the LTC (Order Block)

**Bearish OB LTC**: body (close) takes buy-side — candle closes *above* prior high.
- `close[i] > high[i-1]` ← body consumed buy-side liquidity

**Bullish OB LTC**: body (close) takes sell-side — candle closes *below* prior low.
- `close[i] < low[i-1]`

### Step 2 — Find the HPFS Candle

Identical to the RB variant — scan forward for the first candle whose extreme is
inside the LTC body:

- **Bearish**: `high[j] < open[i]` → HPFS level = `high[j]`
- **Bullish**: `low[j] > open[i]`  → HPFS level = `low[j]`

The OB HPFS level is the high of the first candle that falls back inside the OB
candle's body — it is a failure swing within the distribution zone of the order
block.

---

## Key Distinction

| | RB HPFS | OB HPFS |
|---|---|---|
| What takes liquidity | Wick | Body (close) |
| LTC condition (bearish) | `high > prior_high` AND `close < prior_high` | `close > prior_high` |
| HPFS scan condition | `high[j] < open[LTC]` | `high[j] < open[LTC]` |
| LTC structure | Rejection block (wick sweep) | Order block (body through) |

Both share the same HPFS detection step — the distinction is entirely in how the
LTC is identified.

---

## Validity

- The HPFS level must remain untested (no subsequent candle takes it) to stay
  active. Once taken, it is consumed and the process restarts.
- Invalidation: any candle closes beyond the HPFS level in the direction of the
  original sweep (e.g., closes above the HPFS high for a bearish setup).

---

## Recursive Property

A HPFS level is itself a liquidity pool. When price returns and sweeps the HPFS
level, the identical process restarts:

1. HPFS level exists as resting liquidity
2. A new LTC sweeps through that HPFS level (wick for RB, body for OB)
3. First subsequent candle with extreme inside the new LTC body = new HPFS

In a sustained down leg you will see stair-stepping HPFS highs, each created by
the raid of the prior one.

---

## Relationship to Swing Without Liquidity

The complement concept is [[swing-without-liquidity]] — a swing that already consumed
a prior swing. Those are disqualified as DOL candidates because the liquidity there has
already been distributed. HPFS is what remains after filtering those out.

---

## Relationship to Draw on Liquidity

HPFS levels are a valid source of DOL (see [[draw-on-liquidity]]). A HPFS high
fits Kishane's pool validity rule — it is a high that formed without sweeping
above a prior high, making it untouched buy-side that the algorithm is likely
to deliver price toward.

---

## Detection Rules (Implementation Notes)

```python
# RB HPFS — wick takes
def rb_ltc_bearish(i): return high[i] > high[i-1] and close[i] < high[i-1]
def rb_ltc_bullish(i): return low[i]  < low[i-1]  and close[i] > low[i-1]

# OB HPFS — body takes
def ob_ltc_bearish(i): return close[i] > high[i-1]
def ob_ltc_bullish(i): return close[i] < low[i-1]

# HPFS scan — same for both variants
def find_hpfs_candle(ltc_bar, direction, scan_forward=6):
    for j in range(ltc_bar + 1, ltc_bar + 1 + scan_forward):
        if direction == 'bearish' and high[j] < open[ltc_bar]:
            return j, high[j]    # HPFS candle index, HPFS level
        if direction == 'bullish' and low[j] > open[ltc_bar]:
            return j, low[j]
    return None

# Validity check
def hpfs_active(hpfs_bar, direction, untested_bars=20):
    if direction == 'bearish':
        return max(high[hpfs_bar+1 : hpfs_bar+1+untested_bars]) < high[hpfs_bar]
    return min(low[hpfs_bar+1 : hpfs_bar+1+untested_bars]) > low[hpfs_bar]
```

Parameters:
- `scan_forward` (default 6): bars after LTC to search for the HPFS candle
- `untested_bars` (default 20): bars to check for consumption after formation

---

## Sources

- User observation / chart annotation — session 2026-06-14
- Consistent with Kishane's "failure strings excluded" pool validity rule in
  draw-on-liquidity.md (see Section 2, Pool validity rule)
