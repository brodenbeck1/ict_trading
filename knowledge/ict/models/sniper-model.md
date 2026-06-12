---
name: sniper-model
aliases: [sniper, daily bias model, ICT sniper]
category: models
related: [daily-bias, liquidity-sweep-stop-hunt, smt-divergence, market-structure-shift]
parameters:
  daily_lookback: 20
  dealing_range_days: 20
  swing_lookback: 3
  rejection_window_bars: 12
detection: implemented
---

# Sniper Model

A four-component ICT bias + entry checklist. All four must align (rule of
exclusion); SMT is a confirmation weight, not a hard gate.

1. **HTF daily bias** — order flow + draw-on-liquidity + premium/discount agree
   on direction. See [daily-bias](../daily-bias/daily-bias.md).
2. **Liquidity sweep** — a session extreme (prior high/low) is raided and then
   rejected; price must close back inside within `rejection_window_bars`.
   See [liquidity-sweep-stop-hunt](../liquidity/liquidity-sweep-stop-hunt.md).
3. **SMT divergence** — at least one correlated index (ES/NQ/YM) fails to
   confirm the sweep extreme. Adds conviction; absence is noted but does not
   invalidate the setup. See [smt-divergence](../entries/smt-divergence.md).
4. **Market structure shift** — a prior swing is broken with displacement after
   the sweep, confirming the reversal. See [market-structure-shift](../market-structure/market-structure-shift.md).

## Detection Rules

- Compute daily bias on the higher-timeframe daily bars before each session.
- Sweep direction: `high` for bearish bias, `low` for bullish bias.
- Level swept: prior daily high/low (index -2 of daily bars).
- MSS must occur after the sweep (`sweep_time` is the anchor).
- Output: `{bias, ohlc_profile, stop_hunt, smt, mss, targets, checks, actionable}`.
