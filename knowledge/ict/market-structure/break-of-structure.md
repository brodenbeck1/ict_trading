---
name: break-of-structure
aliases: [BOS, BMS, break of market structure]
category: market-structure
related: [swing-points, market-structure-shift, displacement]
parameters:
  break_rule: "close beyond the swing level (wick-only breaks are sweeps, not structure breaks) — config flag close_vs_wick"
detection: not-implemented
---

# Break of Structure (BOS / BMS)

Price breaks a significant swing level **in the direction of the prevailing trend** —
a new higher high in an uptrend or lower low in a downtrend. BOS is the continuation
event: it confirms the existing delivery direction remains intact and extends the
dealing range.

Distinguish from [market-structure-shift](market-structure-shift.md): an MSS breaks
structure **against** the trend (potential reversal); BOS breaks it **with** the trend
(continuation). Older ICT material (and this project's first strategy note) uses
"Break of Market Structure (BMS)" loosely for any significant swing break — in the
library taxonomy, classify by direction relative to trend: with-trend = BOS,
counter-trend with displacement = MSS.

Related early-era term — **market flow**: the trend state defined by only the *most
recent* swing pair (recent swing high broken ⇒ flow bullish until the most recent
swing low breaks; old swings disregarded). The 2020 forex notes' alignment rule maps
to this file's trend state machine: D1/H4/H1 flow in agreement = tradeable; structure
and flow in conflict or unclear = stand aside.

## Detection Rules

- Maintain trend state from the swing series (HH/HL sequence = up; LH/LL = down).
- Bullish BOS: `close[t] > last_confirmed_swing_high` while trend == up.
- Wick-only violation that closes back inside = liquidity sweep of the swing, not BOS.
- Emit: {time, level_broken, direction, trend_state_before} and update the swing/trend
  state machine.

## Sources

- [MSS vs BOS — equiti.com](https://www.equiti.com/sc-en/news/trading-ideas/mss-vs-bos-the-ultimate-guide-to-mastering-market-structure/)
- [Market Structure Shift in ICT — fxopen.com](https://fxopen.com/blog/en/market-structure-shift-meaning-and-use-in-ict-trading/)
- [MSS explained — icttrading.org](https://icttrading.org/market-structure-shift/)
- "Market flow" terminology: `strategies/notes/ict-forex-notes-mmari-2020.md` §3
