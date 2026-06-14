---
name: break-away-gap
aliases: [BAG, breakaway gap, break away FVG]
category: price-action
related: [failure-swing, swing-without-liquidity, draw-on-liquidity]
ict_refs: [fair-value-gap]
source_coverage: partial-public
parameters:
  swing_lookback: 1     # bars each side to confirm a swing point
detection: implemented
---

# Break Away Gap (BAG)

A **break away gap** is a Fair Value Gap that forms on the displacement candle
that trades through a **no-liquidity swing point**.

A no-liquidity swing high (or low) is one whose extreme already consumed the
prior swing's liquidity — stops have been distributed there and no meaningful
resting orders remain (see [[swing-without-liquidity]]). When price **breaks
through** such a level with enough force to leave an FVG, that imbalance is
called a break away gap.

The BAG is significant because:
1. It formed at a level with no resting liquidity to absorb it — price was free
   to accelerate through without stop-hunt resistance.
2. The FVG left behind marks the origin of that acceleration — a valid
   re-entry zone if price retraces.
3. The combination of displacement (FVG) and a no-liquidity break signals
   genuine order flow, not a stop hunt reversal.

---

## Detection Rules

### Bullish BAG

1. Identify all swing highs via `SwingPointScanner` (lookback = 1).
2. Classify consecutive swing highs with `classify_swing_liquidity`:
   - `no_liquidity` if `high[i] > high[i-1]` (took prior high)
3. Scan for bullish FVGs: `candle[i+1].low > candle[i-1].high`.
4. A bullish FVG whose **gap top** (`candle[i+1].low`) reaches into or above
   a prior `no_liquidity` swing high → **Bullish BAG**.
   - `fvg.top >= no_liquidity_swing_high`
   - A gap whose top ends below the swing does not qualify — the wick may
     have crossed but the imbalance did not.
5. Each no-liquidity swing generates at most one BAG; the swing is consumed
   on first use and ignored for all later FVGs.

### Bearish BAG

Mirror of the above using swing lows:
1. `no_liquidity` low: `low[i] < low[i-1]` (took prior low).
2. Bearish FVG: `candle[i-1].low > candle[i+1].high`.
3. A bearish FVG whose **gap bottom** (`candle[i+1].high`) reaches into or
   below a prior `no_liquidity` swing low → **Bearish BAG**.
   - `fvg.bottom <= no_liquidity_swing_low`
4. Same one-BAG-per-swing deduplication rule applies.

---

## Validity

- The BAG zone remains valid until price **closes through** the far edge:
  - Bullish BAG top = `candle[i+1].low`; invalidated by a close below the bottom.
  - Bearish BAG bottom = `candle[i+1].high`; invalidated by a close above the top.
- A BAG that has been fully mitigated (price returned and filled the gap)
  is consumed — do not re-use.

---

## Relationship to Other Concepts

- **[[swing-without-liquidity]]** — supplies the no-liquidity swing points
  that gate BAG formation.
- **[[failure-swing]]** (HPFS) — the complement: swings that did NOT take a
  prior extreme. BAGs form through the no-liquidity swings, not the HPFS ones.
- **[[draw-on-liquidity]]** — a BAG within the DOL corridor is a high-quality
  re-entry zone; a BAG outside it is lower priority.

---

## Sources

- User observation / chart annotation — session 2026-06-14
