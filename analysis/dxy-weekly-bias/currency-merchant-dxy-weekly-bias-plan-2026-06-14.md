# Currency Merchant — DXY Weekly Bias Plan

**Model**: currency-merchant
**Concept**: dxy-weekly-bias
**Instrument**: DXY → NQ/ES/YM (index bias)
**Analysis date**: 2026-06-14
**Status**: in-progress

---

## Hypothesis

DXY weekly liquidity pool reactions (MSS or CISD at a recently raided valid pool) can
determine the weekly directional bias for NQ. Bearish DXY reaction → bullish NQ bias.
Bullish DXY reaction → bearish NQ bias.

Pool hierarchy: yearly > quarterly > monthly > weekly > daily. Weekly swings on DXY
are the primary reference level for this study.

---

## Build Plan

### Step 1 — Weekly DXY swing extraction
- Resample DXY daily CSV → weekly OHLC
- Run `SwingPointScanner` on weekly bars to get swing highs and lows
- **Files**: `src/ict/data/loader.py` (already has `read_DXY()`), `src/ict/concepts/market_structure.py`

### Step 2 — Valid pools via pool_validity
- Apply `filter_failure_strings` on weekly swing highs (buy-side) and lows (sell-side)
- Filter by weekly open: bullish bias → only pools above weekly open; bearish → below
- **Files**: `src/ict/concepts/pool_validity.py` (complete)

### Step 3 — Most recently raided pool
- Use `find_raid_bar` to identify which valid pool was most recently taken on DXY weekly
- That raided pool is the level where we analyze the reaction
- **Files**: `src/ict/concepts/pool_validity.py` (complete)

### Step 4 — Reaction classifier (primary build target)
Given the raided pool timestamp + DXY bars after the raid, classify the reaction:

#### 4a. MSS (Market Structure Shift)
- Existing `detect_mss` in `market_structure.py` — **already implemented**
- Requires: break of opposite swing with displacement after the raid
- Confirm it works on weekly DXY bars

#### 4b. CISD (Change in State of Delivery)
- Currently `not-implemented` in knowledge
- Definition: identify the consecutive same-color candles that made the sweep leg;
  reference = open of the first candle in that series (strictest = highest open for bullish)
- Bullish CISD: `close[t] > reference_open` after sweep low is in place
- Need to write `detect_cisd` in `market_structure.py` and update knowledge file
- **Decision**: test MSS vs CISD separately to see which is more predictive

### Step 5 — `dxy_weekly_bias()` output
- Raided buy-side (high) pool + bearish reaction (MSS/CISD down) → DXY bullish → **indices bearish**
- Raided sell-side (low) pool + bullish reaction (MSS/CISD up) → DXY bearish → **indices bullish**
- New file: `src/ict/concepts/dxy_bias.py`
- New knowledge: `knowledge/currency-merchant/price-action/dxy-bias.md`

### Step 6 — Backtest against NQ
- For each week in dataset: compute `dxy_weekly_bias()` → compare against NQ weekly direction
- Measure accuracy: % of weeks where DXY bias correctly predicted NQ direction
- Break down by signal type (MSS vs CISD) and pool type (weekly swing high vs low)
- **Files**: new script `backtests/dxy_bias_accuracy.py`

---

## Open Questions

1. MSS vs CISD — which reacts better on weekly DXY bars? (test both)
2. How many bars after the raid to wait for reaction confirmation?
3. Does the pool hierarchy (weekly vs monthly vs quarterly DXY swings) improve accuracy?
4. What lookback window for SwingPointScanner on weekly DXY (default=1 too noisy)?

---

## Current Step

**Step 4a** — Define MSS precisely, confirm `detect_mss` behavior on weekly DXY bars,
then write `detect_cisd`.
