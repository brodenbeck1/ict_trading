---
name: dark-pool
aliases: [DP, dark pool gap, dark liquidity zone]
category: price-action
related: [break-away-gap, swing-without-liquidity, draw-on-liquidity]
ict_refs: [fair-value-gap]
source_coverage: partial-public
parameters:
  swing_lookback: 1     # bars each side to confirm a swing point
detection: implemented
---

# Dark Pool

A **dark pool** is a hidden imbalance zone that forms when price trades through a
**no-liquidity swing point** without leaving a formal Fair Value Gap.

It is the complement of the [[break-away-gap]]:
- **BAG**: price rips through the no-liq swing AND leaves a 3-candle FVG — the imbalance is visible.
- **Dark Pool**: price clears the no-liq swing cleanly — no 3-candle gap, but an implied zone of
  thin delivery still exists between the old swing level and where price now sits.

---

## Zone Definition

### Bullish Dark Pool

1. Identify a no-liquidity swing high at level **H** (see [[swing-without-liquidity]]).
2. Scan forward for the **first candle whose LOW is above H** — this is the displacement candle.
   (`candle.low > H`)
3. **Dark Pool zone**: `bottom = H`, `top = candle.low`
4. The zone captures the space price "skipped over" — delivered without leaving an imbalance.
5. **Exclusion**: if the displacement candle also produces a bullish FVG that reaches H
   (`fvg.top >= H`) → this is a [[break-away-gap]], not a dark pool.

### Bearish Dark Pool

Mirror of the above using swing lows:

1. No-liquidity swing low at level **L**.
2. First candle whose HIGH is below L — the displacement candle. (`candle.high < L`)
3. **Dark Pool zone**: `bottom = candle.high`, `top = L`
4. Exclusion: if the displacement candle produces a bearish FVG reaching L (`fvg.bottom <= L`) →
   [[break-away-gap]], not a dark pool.

---

## Detection Rules

Implemented in `src/ict/concepts/dark_pool.py` → `find_dark_pools(df, direction, swing_lookback)`.

For each no-liquidity swing (using `classify_swing_liquidity`):
1. Search bars after the swing for the first candle that clears it (low > H for bullish, high < L for bearish).
2. Check whether that displacement candle is also the centre of a qualifying BAG.
   - Bullish: `candle[i+1].low > candle[i-1].high` AND `candle[i+1].low >= H` → BAG → skip
   - Bearish: `candle[i-1].low > candle[i+1].high` AND `candle[i+1].high <= L` → BAG → skip
3. If not a BAG, record a `DarkPool` with the zone and the swept swing metadata.
4. Each no-liquidity swing generates at most one dark pool (first displacement wins).

---

## Validity

- Zone remains open until price **closes through** the far edge:
  - Bullish DP: invalidated by close below `bottom` (the no-liq swing high).
  - Bearish DP: invalidated by close above `top` (the no-liq swing low).
- A fully mitigated dark pool is consumed — do not re-use.

---

## Relationship to Other Concepts

- **[[break-away-gap]]** — when a displacement through a no-liq swing leaves a formal FVG, that FVG
  is a BAG. A dark pool is the alternative: same trigger, no formal gap.
- **[[swing-without-liquidity]]** — provides the no-liq swing points that gate both BAG and DP formation.
- **[[draw-on-liquidity]]** — a dark pool within the DOL corridor is a high-quality re-entry zone.

---

## Sources

- User observation / chart annotation — session 2026-06-14
