---
name: draw-on-liquidity
aliases: [DOL, draw, drone liquidity, drawn liquidity, liquidity draw, weekly draw]
category: price-action
related: [pa-flow, imbalances-to-liquidity, rules-of-engagement, cycle-order-flow, session-opens]
ict_refs: [draw-on-liquidity, buy-side-liquidity, sell-side-liquidity, liquidity-sweep-stop-hunt, order-block, fair-value-gap, market-structure-shift]
source_coverage: partial-public
parameters:
  weekly_bias_tool: "DXY direction — bearish DXY = bullish indices, bullish DXY = bearish indices"
  reference_point: "weekly open (Sunday open, or 4 AM NY Monday)"
  daily_stop_rule: "if bullish, an old daily low must be taken before the run higher (and vice versa)"
  trade_start_time: "08:00 NY (not before)"
  london_close_caution: "10:00–12:00 NY — profits being taken, high reversal risk"
  valid_pool_rule: "a high/low only qualifies as DOL if it did NOT already take a previous high/low (failure strings excluded)"
detection: not-implemented
---

# Draw on Liquidity (DOL) — Weekly Framework

Kishane's core organizing principle: every trading day's job is to find a setup that moves
price toward the **weekly draw on liquidity** — the untested pool that the algorithm is
being delivered to that week. The concept ties together bias, daily order flow, intraday
entry, and session timing into a single top-down hierarchy.

> "We're essentially trying to capitalize on the weekly expansion. We're not trying to
> trade the monthly high or monthly low. We're just trying to go in on a daily basis and
> frame a setup that's high probability and lightly drawn towards our weekly objective."

---

## 1. Weekly Bias — DXY First

Before identifying the DOL, determine **weekly directional bias** from the DXY:

- **Bearish DXY** → expect bullish indices (ES/NQ/YM)
- **Bullish DXY** → expect bearish indices
- DXY is the most consistent approach for weekly bias according to Kishane
- Focus on high-impact USD events: FOMC, interest rate, jobs data (red-folder news on the
  economic calendar)
- Apply the same DOL analysis *to DXY* to understand where it's being delivered

---

## 2. Identifying the Weekly Draw

The weekly open (Sunday / 4 AM NY Monday) is the **reference point** — the algo looks back
from here to find what it will deliver price to.

### Bullish week (DXY bearish)
- All candidate pools must be **above** the weekly open — ignore price below it
- Look left for pools that meet the validity rule (see below)
- The first draw is the nearest valid pool above; further draws become relevant after price
  closes above the first

### Bearish week (DXY bullish)
- All candidate pools must be **below** the weekly open

### Pool validity rule — "failure strings" excluded
A high or low only counts as liquidity **if it did NOT already take a previous swing high/low**:
- A high that took out the prior high = a "failure string" — no unfilled orders sitting
  there, already distributed
- A high that did **not** take a prior high = valid buy side — orders likely still resting

> "I never considered these daily highs as liquidity draw because they took out previous
> liquidity. This would be liquidity because none of these took a previous weekly high."

Common valid pool types above weekly open (bullish):
- FVG / CV (fair value gap / consequent void) from a prior selling leg — business was
  left undone at that price level
- Failure swing high (approached but never closed above the draw)
- Relative equal highs that have not yet been taken

---

## 3. Bookmaking — the Delivery Logic

Kishane frames the week as a "book" the algo is filling:

| Book type | Accumulation side | Distribution side |
|---|---|---|
| **Long book** | Sell side (lows) | Buy side (highs) above |
| **Short book** | Buy side (highs) | Sell side (lows) below |

For a bullish week (long book): price must first accumulate at sell side (take a daily low)
**then** distribute to the buy side draw above.

---

## 4. Liquidity Pool Close Confirmation Rule

This rule governs both the "last stop on true" direction read and the failure swing /
continuation determination. Whenever price reaches any liquidity pool, evaluate the
**closing behavior** to determine what comes next.

### Close past the pool → Continuation

Price closes **beyond** the pool level (closed above a buy side pool, or closed below a
sell side pool) → expect continuation in that direction. The pool has been consumed and
the algo is delivering further.

### Wick or close-then-fail → Reversal / Retracement setup

Two conditions that signal reversal rather than continuation:

1. **Wick only**: price pierces the pool intrabar but the candle closes back on the other
   side — the pool was not genuinely consumed
2. **Close-then-fail**: price closes past the pool but a subsequent candle closes back
   through that candle's originating side (e.g., a close below the buy-side pool, then a
   candle closes below that candle's low) — the initial close was a false break

**Bullish reversal confirmation** (after sell side pool):
- Wick into sell side pool (close stays above), OR close below pool then get reclaimed
- **Then**: subsequent candle(s) close **above the high of the candle that reached/crossed
  the pool**
- → Confirmed bullish bias, look for buy DOL

**Failure threshold**: 3 consecutive candles reaching the DOL without closing past it →
expect an opposing liquidity run before continuation. The DOL itself remains valid; price
just needs to sweep the other side first.

---

## 5. Daily Order Flow Process

After framing the weekly draw, go to the **daily chart** each session:

1. **Identify daily draw** — the nearest valid pool in the direction of the weekly draw
2. **Apply the close confirmation rule** at each pool encountered:
   - Pool closed past → continuation toward the next draw
   - Pool wicked or close-then-failed → opposing liquidity run coming; wait for reversal
     confirmation before entering
3. **Daily opposing liquidity run first (if bullish)**: an old daily low must typically be
   taken before price runs to the draw
   - Monday low taken on Tuesday → run higher → pattern repeats across the week

> "Last stop on true: I don't buy or sell the market if buy side liquidity is above me.
> If I see this where we took this low and I'm bullish, I'm likely looking for longs
> after the stop hunt."

### Daily failure swing
- Price reaches draw but does not close past it (wick or close-then-fail)
- 3 candles failing to close through = trigger to expect opposing liquidity run
- After the opposing sweep, re-evaluate the same draw — it remains valid
- On a consolidation, pair daily draws with equilibrium (50% of daily range)

---

## 5. Intraday Entry Process (5m / 1H)

### Session windows
| Time (NY) | Role |
|---|---|
| 4:00 AM | Forum open — mark open line |
| 8:00 AM | **Trade start** — first look for setups |
| 9:30 AM | RTH open — noted but Kishane cares less about it |
| 10:00–12:00 | London close — **reversal / profit-taking zone, avoid new longs** |
| 11:00 AM | End of trade window marker |

**Do not trade before 8 AM.**

### Intraday DOL identification
When the weekly draw is not visible on the 5m chart (too far away), identify **intraday
buy side** from highs that formed **to the left of 8 AM**:
- These become the immediate intraday draw
- If price closes above the intraday draw, look for the next pool higher
- Price inside a range is not bounded by the time it formed — use the full candle data
  from before 8 AM as the dealing range

### "Fair value for buying" — entry refinements
Kishane's concept for where long orders should ideally enter within a bullish range:

1. **Equilibrium (50%)** of the dealing range — first anchor
2. **Order block high / open** inside the dealing range — ICT-compatible OB with bullish
   order flow context
3. **Short-term sell side pool** inside the dealing range (internal liquidity) when the
   larger structure is bullish
4. **4 AM open confluence** with 8 AM open — both lines at the same level = strong confluence

### Confirmation before entry
After 8 AM, two things must be true for a long entry:
1. **Sell side liquidity taken** (internal or daily, depending on what's needed)
2. **Change in state of delivery** — e.g., down candle's high is traded through on a
   subsequent candle, validating bullish order flow

> "Opportunities are born from a change in a state of delivery. Market is bullish — this
> is short-term delivery in the opposite direction. I want to go along."

Entry trigger: **trade above the high of the order block candle** (the down candle inside
the range whose high is intact); stop below the order block.

### Failure swing on intraday
- Price runs toward buy side but pulls back without closing above = intraday failure swing
- Look for sell side being taken next (opposing liquidity run), then re-entry

---

## 6. Targets

| Priority | Target |
|---|---|
| 1 (intraday) | Nearest buy side pool above 8 AM open (identified before entry) |
| 2 (daily) | Daily failure swing high (most liquidity in Kishane's view) |
| 3 (weekly) | Weekly draw on liquidity |

- Take **partials at intraday target**, move to **break even**, hold remainder for daily /
  weekly draw
- Kishane does **not trail stops** — the origin of the move rarely gets revisited; leave
  stop at break even and let it run

> "I don't trail stops because that's exactly how internal liquidity is created. The
> origin of the move generally does not find price revisiting after we leave the range."

---

## 7. Filters / Rule of Exclusion

- **Do not trade before 8 AM** — not enough information
- **High-impact news days**: stay out or cut risk significantly
- **Bank / US holidays**: no trades
- **10 AM–12 PM**: London close reversal zone — no new directional entries unless setup is
  exceptional
- **Weekly draw already met**: if the week's draw has been reached and price closes above,
  do not enter a new long without first identifying the *next* draw; probability is low
- **No intraday sell side taken yet**: if bullish and no opposing sell side run has
  happened, do not enter long (wait for the accumulation)
- **Daily close fails to confirm**: if end-of-day close does not close above the intraday
  objective, lower probability — skip or size down next day
- **"If you don't know where the liquidity is, you become the liquidity"**: no setup
  without a clearly identified draw

---

## 8. Edge / Thesis

The algorithm operates as a bookmaker: it accumulates positions at one side of the book
(sell side / stop hunts) and then distributes them to willing participants at the other
side (buy side draws / FVGs). Price is not random — it is delivering from one pool to
another. The edge comes from:

1. Identifying which pool the algo is filling **before** it gets there
2. Waiting for the opposing liquidity sweep to confirm the accumulation phase is done
3. Entering at discount (fair value) in the direction of distribution

The weekly open is the loopback starting point; the DXY establishes the direction of that
delivery; the daily order flow repeats the same structure on a smaller scale each day.

---

## Detection Rules

- **Weekly draw candidates**: scan highs (bullish) / lows (bearish) above / below the
  weekly open; filter out any that already took a prior swing of equal or greater
  magnitude (raid-first filter)
- **Daily opposing liquidity run**: detect when a prior daily low (bullish) is taken
  before the main run — flag as accumulation complete
- **Intraday DOL**: collect all swing highs from the prior session up to 8 AM; earliest
  untested group = immediate draw
- **Fair value for buying**: 50% retracement of the dealing range (entry anchor); OB
  inside the range with intact lows; short-term sell side pool inside the range
- **Confirmation trigger**: down candle followed by a candle closing above that down
  candle's high = change in state of delivery; arm entry above the high

---

## Open Questions

### 1 + 3. ~~"Last stop on true" and failure swings~~ RESOLVED — unified close confirmation rule
**Timestamp**: ~15:57–16:30 (Q1); ~5:34–5:57 (Q3); ~30:52–31:48 (Q3 applied)

**Answer**: Q1 and Q3 are the same mechanism — the **close confirmation rule** (see
Section 4). Whether a pool "counts" as taken depends entirely on closing behavior, not
just whether price touched it.

**Q1 — last stop on true direction read**:
- Buy side pool **closed past** → continuation; now track sell side as next DOL
- Buy side pool **wicked or close-then-failed** → pool not genuinely consumed; bias stays
  or reversal setup forming; look for bullish confirmation (subsequent candle closes above
  the high of the pool-touching candle) → buy DOL active

Screenshot example: green candle with large upper wick sweeps prior swing high but closes
back below it → buy side pool was wicked, not consumed → watch for close confirmation
before committing to sell DOL; if subsequent candles close above that wick candle's high,
bullish bias is confirmed instead.

**Q3 — failure swing threshold**:
- 3 consecutive candles reach the DOL without closing past it → expect opposing liquidity
  run before continuation
- After opposing sweep completes, the same DOL remains valid — re-enter on confirmation

---

### 2. ~~DXY bias — any move or a confirmed weekly draw?~~ RESOLVED
**Timestamp**: ~6:06–7:46

**Answer**: DXY trend direction. Primary read is whether DXY is in a bearish or bullish
trend on the weekly/daily. Additionally, if a **large liquidity pool was recently swept on
DXY**, that sweep itself signals the next trend direction for DXY — and by inversion, for
the indices.

- **Bearish DXY trend** → bullish indices
- **Bullish DXY trend** → bearish indices
- **Large DXY pool just taken** (e.g., major swing high or low swept on DXY) → use that
  sweep as confirmation of the new DXY trend direction, which informs index bias

No requirement to map a full DOL framework onto DXY — trend read plus recent large pool
sweeps are sufficient.

**Watch**: 6:06–7:46 for the DXY explanation.

---

### 3. ~~How many failure swings before weekly bias is invalidated?~~ RESOLVED
**Timestamp**: ~5:34–5:57 (rule stated); ~30:52–31:48 (applied on chart)

**Answer**: **3 consecutive failure candles** (candles that reach the DOL but do not close
above it) triggers the expectation of a retracement or opposing liquidity run. The weekly
bias itself is not necessarily invalidated — price is expected to run the other side first,
then resume the original draw.

Rule as stated:
- Price reaches identified DOL
- If it does **not close above** (bullish) / **below** (bearish) → anticipate retracement
  or price going the other direction
- Starting threshold: **3 candles** failing to close through the level

After the opposing sweep completes, the original draw remains valid and the setup resets —
re-evaluate for an entry toward the same DOL.

**Watch**: 5:34–5:57 for the if/then framing; 30:52–31:48 for a live failure swing
example.

---

### 4. Dealing range — prior session or pre-8 AM candles?
**Timestamp**: ~26:04–28:07

*Deferred — will be defined as a separate concept later.*

**What's known so far**: The dealing range is defined by a swing low and swing high that
formed **before 8 AM**, regardless of when those candles printed. Price inside the range
is not bounded by clock time — any structure from before 8 AM is valid as the range.

**Watch**: 26:04–28:07 for the full explanation when ready to formalize.

---

### 5. "4 AM + 8 AM confluence" — alignment rule
**Timestamp**: ~48:58–49:08 (explicit mention); ~34:44–35:00 (applied)

*Deferred — will be defined as a separate "balanced range" concept later.*

**What's known so far**: when the 4 AM open and the 8 AM open coincide or are very close
in price, Kishane treats that zone as a stronger reference point for entries. It appears
to be an additive confluence filter on top of existing conditions (sell side taken, OB
valid), not a standalone reason to enter.

**Watch**: 48:58–49:10 for the clearest statement; 34:37–35:10 for an applied example.

---

## Sources

- Transcript: "Trade Planning | Day Trading" (The Currency Merchant / Kishane Robinson,
  YouTube) — pasted by user 2026-06-14
- Covers: weekly DOL framework, daily order flow, bookmaking concept, fair value for
  buying, intraday entry process, session filters
