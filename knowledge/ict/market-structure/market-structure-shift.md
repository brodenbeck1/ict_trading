---
name: market-structure-shift
aliases: [MSS, CHoCH, change of character, shift in market structure]
category: market-structure
related: [swing-points, break-of-structure, displacement, liquidity-sweep-stop-hunt, change-in-state-of-delivery, break-away-gap, dark-pool]
parameters:
  requires_displacement: true
  requires_prior_sweep: "true in reversal models (sweep -> MSS is the canonical sequence)"
  working_timeframes: "1m/3m/5m for intraday entries; 15m for swing context"
detection: implemented
---

# Market Structure Shift (MSS)

A **counter-trend** confirmation that delivery has reversed. There are two valid forms:

---

## Type 1 — Swing-Level Break (classic)

1. Price sweeps a liquidity pool (e.g., runs buy stops above equal highs);
2. Price then breaks the most recent opposing swing low (bearish) / swing high (bullish)
   with an energetic displacement candle;
3. That break is the MSS.

A weak, grinding break without displacement is *not* a Type 1 MSS — it's noise or a
deeper pullback. SMC's "CHoCH" (change of character) is the same event under a different
name.

---

## Type 2 — Close Past an Opposing BAG or Dark Pool

An alternative confirmation that does **not** require a swing-level break:

- **Bearish MSS Type 2**: after a high sweep, a candle **closes below the bottom** (far
  edge) of a previously formed **bullish** [Break Away Gap](break-away-gap.md) or
  [Dark Pool](dark-pool.md). The bullish zone was created on prior upward delivery; price
  returning and closing back through its bottom confirms bearish delivery has taken over.
- **Bullish MSS Type 2**: after a low sweep, a candle **closes above the top** of a
  previously formed **bearish** BAG or Dark Pool. Same logic in reverse.

The logic: BAGs and Dark Pools are imbalances left by prior displacement. When price
returns and **closes through** the far edge of one, it proves the algorithm is now
delivering in that direction — structure has shifted even if no clean swing exists to break.

---

## Detection Rules

### Type 1
- Bearish: `close[t] < last_confirmed_swing_low` after a sweep of highs.
- Bullish: `close[t] > last_confirmed_swing_high` after a sweep of lows.
- Time-link: `sweep_time < mss_time <= sweep_time + max_bars` (e.g. 30 bars on 1-5m).
- The swing broken should be the swing that *originated* the sweep leg.

### Type 2
- Bearish: `close[t] < bag.fvg.bottom` for any **bullish** BAG formed before bar `t`, OR
  `close[t] < dp.bottom` for any **bullish** Dark Pool formed before bar `t`.
  The bullish zone was formed on prior upward delivery; closing back below its bottom
  confirms bearish delivery has taken over.
- Bullish: `close[t] > bag.fvg.top` for any **bearish** BAG formed before bar `t`, OR
  `close[t] > dp.top` for any **bearish** Dark Pool formed before bar `t`.
  Same logic in reverse — closing above the top of a bearish zone confirms bullish delivery.
- The BAG/DP direction is always **opposite** to the MSS direction.
- Same time-link window as Type 1 when a prior sweep is given.
- Emit: {time, broken_level, direction, sweep_ref, mss_type, pd_array_kind}.

Both types emit the same result schema; `mss_type` field distinguishes them.

## Sources

- [ICT Market Structure Shift — innercircletrader.net](https://innercircletrader.net/tutorials/ict-market-structure-shift/)
- [MSS meaning & use — fxopen.com](https://fxopen.com/blog/en/market-structure-shift-meaning-and-use-in-ict-trading/)
- [MSS vs BOS — equiti.com](https://www.equiti.com/sc-en/news/trading-ideas/mss-vs-bos-the-ultimate-guide-to-mastering-market-structure/)
- [MSS in SMC/ICT — tradingfinder.com](https://tradingfinder.com/education/forex/ict-mss/)
