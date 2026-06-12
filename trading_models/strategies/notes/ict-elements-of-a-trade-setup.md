# Strategy: ICT Elements of a Trade Setup

**Source**: YouTube — ICT (Inner Circle Trader), "Elements to a Trade Setup" (first teaching episode)
**Date extracted**: 2026-06-06
**Status**: Rules finalized — ready to code

---

## Overview

The foundational ICT intraday setup for index futures. Algorithms engineer liquidity by sweeping stop pools in the opposite direction of the intended move, then deliver price efficiently via a Fair Value Gap. The trader enters on the retracement into the FVG after a confirmed market structure break, targeting the nearest opposing liquidity pool or imbalance below the 50% level of the current range.

## Instruments

- **Primary**: NQ (E-mini Nasdaq futures) — most volatile, most handles per move
- **Correlated**: ES (E-mini S&P), YM (E-mini Dow) — used for context, potential SMT confirmation
- Also tradeable on ES and YM with the same logic

## Timeframes

| Role | Timeframe | Purpose |
|---|---|---|
| Bias | Weekly | Direction the weekly candle is expected to expand (higher or lower) |
| Context | Daily | Swing highs/lows = liquidity pools, draw on liquidity, old lows/highs as targets |
| Structure | 1H | Session framework, weekly range mapping, short-term swing highs/lows |
| Confirmation | 15m | Relative equal highs/lows, stop hunt identification, BMS setup |
| Entry | 2m (or 1m/3m) | Fair Value Gap identification, entry trigger |

## ICT Concepts Used

- **Weekly bias** — expected direction of weekly candle expansion
- **Draw on liquidity** — where price is magnetically attracted (old highs/lows, imbalances)
- **Buy stops / sell stops** — resting above old highs and below old lows respectively
- **Liquidity engineering** — fake move in one direction to trap traders before the real move
- **Relative equal highs/lows** — two or more highs/lows at approximately the same price = retail buy/sell stops clustered there
- **Break of Market Structure (BMS)** — a short-term swing low is broken to the downside (bearish) or swing high broken to the upside (bullish)
- **Fair Value Gap (FVG)** — three-candle imbalance: candle 1's high and candle 3's low do not overlap (gap in the middle); the displacement candle creates it after the BMS
- **Premium / Discount Matrix** — 50% of a defined range; selling in premium (above 50%), buying in discount (below 50%)

## Entry Checklist — Bearish Example (all must be true in order)

1. **Weekly bias is bearish** — the weekly candle is expected to expand lower based on: prior week's structure, seasonality, macro context, ongoing downtrend
2. **Daily chart shows a draw on liquidity below** — an old daily low, imbalance, or cluster of sell stops is the target level
3. **On the hourly chart**: map the weekly session range (Monday midnight open to Friday close). Identify the short-term high and short-term low within the consolidation
4. **Liquidity engineering occurs**: price drops first, taking out sell stops below the short-term low (trapping breakout shorts)
5. **Buy stop run**: price reverses and drives up through the relative equal highs (the short-term high), triggering buy stops — these are the counterparty for institutional shorts
6. **Drop to 15m or 2m**: after buy stops are taken, confirm the stop hunt is complete (price is now in premium relative to the session range)
7. **Break of Market Structure (BMS) on 2m**: a short-term swing low is broken to the downside — this is the algorithm's signal that the sell program is executing
8. **Fair Value Gap identified**: the displacement candle that broke the swing low created a FVG (candle N-1 high to candle N+1 low, with candle N only moving down)
9. **Price retraces into the FVG** — enter short as price trades up into this imbalance zone

**Entry trigger**: Short limit order at or near the FVG, as price retraces into it

## Stop Loss

Above the swing high that was swept (the buy stop level that was run). Options depending on risk tolerance:
- Tight: above the FVG candle's high
- Standard: above the short-term swing high that was taken

## Targets

1. **Primary**: nearest old low or imbalance **below the 50% level** of the current session range — low-hanging fruit, take this first
2. **Secondary**: the daily old low (the major draw on liquidity) — only trail into this if the move is clearly running; don't hold for it as the primary objective
3. **Rule**: do not aim for distant targets — take what the market offers at the nearest opposing level

## Session / Time Filters

- **Best window**: 8:30 AM – 11:00 AM New York time (NY pre-market open through mid-morning)
- **Frequency**: one quality setup per session is sufficient; do not force trades outside the window
- **Frequency per week**: look for one or two setups per week, not every day — consistency over frequency

## Filters — Rule of Exclusion

- No weekly bias established → no trade
- No identifiable draw on liquidity (no clear old low/imbalance target) → no trade
- No liquidity engineering / stop hunt occurred → wait, do not enter on the first break
- No BMS on lower timeframe after the stop hunt → no trade
- No FVG formed by the displacement candle → no entry (don't enter a trending move without an imbalance)
- Outside the 8:30–11:00 NY time window → skip (especially while developing)
- Price has already moved significantly from the FVG → do not chase; if price has taken out the first target low, do not enter late

## Edge / Thesis

Algorithmic price delivery is not random — it follows a mechanical sequence of liquidity engineering then efficient rebalancing. Before any significant directional move, the algorithm sweeps the opposing stop pool to create the counterparty for institutional order flow. The FVG left by the displacement move is the algorithm's footprint. When price retraces into that FVG, it is the final inefficiency being closed before the next leg delivers. Entering there puts the trader inside the algorithm's delivery window with a defined invalidation point (the swept stop level).

## Decisions (resolved 2026-06-06)

| Question | Decision |
|---|---|
| Swing definition for BMS | **3-bar swing** — candle N is a swing low if its low is lower than both candle N-1 and candle N+1 |
| Relative equal highs/lows tolerance | **Dynamic: starts at 20 NQ points**, configurable per instrument |
| Entry at FVG | **Limit at the top of the FVG** (bearish: top = candle N-1 high; bullish: bottom = candle N-1 low) |
| Stop placement | **At the high/low of the swing high/low** that was swept in the stop hunt |
| SMT divergence | **Not part of this model** — will be layered into a separate model |

## Open Questions

All questions resolved — see Decisions table above.

| Additional Question | Decision |
|---|---|
| FVG minimum size | **Any gap qualifies** — no minimum size filter |
| Multiple FVGs after BMS | **Either FVG is valid** — use the first one price retraces into |
| Liquidity engineering fake-out required | **Not required** — any buy-stop sweep + BMS + FVG qualifies, regardless of prior sell-stop fake-out |

## Notes

- ICT introduced the Fair Value Gap concept in 2016; this lesson is from his early YouTube mentorship series
- The 50% premium/discount concept uses a simple Fibonacci dragged from the low to the high of the current range — no indicator needed
- "Low-hanging fruit" principle: always target the nearest liquidity, not the farthest — the farthest target is a bonus, not the plan
- The micro contracts (MNQ, MES, MYM) are the recommended vehicle while developing — smaller tick multiplier limits dollar risk while learning
- ICT explicitly does NOT teach scalping for 3–5 handles; the target is significant intraday legs (20–100+ handles on NQ)
- Homework from video: go through historical intraday charts on all three indices, find BMS + FVG patterns, log how many handles each offered
