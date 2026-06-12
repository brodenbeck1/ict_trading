---
name: market-structure-shift
aliases: [MSS, CHoCH, change of character, shift in market structure]
category: market-structure
related: [swing-points, break-of-structure, displacement, liquidity-sweep-stop-hunt, change-in-state-of-delivery]
parameters:
  requires_displacement: true
  requires_prior_sweep: "true in reversal models (sweep -> MSS is the canonical sequence)"
  working_timeframes: "1m/3m/5m for intraday entries; 15m for swing context"
detection: not-implemented
---

# Market Structure Shift (MSS)

A **counter-trend** break of a significant swing level **with displacement** — the
confirmation that delivery has reversed. The canonical reversal sequence:

1. Price sweeps a liquidity pool (e.g., runs buy stops above equal highs);
2. Price then breaks the most recent opposing swing (a short-term low) with an
   energetic displacement candle;
3. That break is the MSS — the algorithm's tell that a sell (or buy) program is now
   running. Entries are then sought on the retrace into the PD array (FVG/OB) left by
   the displacement leg.

A weak, grinding break without displacement is *not* an MSS — it's noise or a deeper
pullback. SMC's "CHoCH" (change of character) is the same event under a different name.

## Detection Rules

- Bearish MSS: trend/leg is up (or a sweep of highs just occurred) AND
  `close[t] < last_confirmed_swing_low` AND the breaking leg qualifies as
  [displacement](displacement.md) (body/ATR threshold, ideally leaving an FVG).
- Time-link to the sweep: in reversal models require
  `sweep_time < mss_time <= sweep_time + max_bars` (e.g., 30 bars on 1-5m).
- Emit: {time, broken_level, direction, sweep_ref, displacement_metrics, fvg_refs}.
- The swing broken should be the swing that *originated* the sweep leg (the low between
  the equal highs and the sweep high), not an arbitrary older swing.

## Sources

- [ICT Market Structure Shift — innercircletrader.net](https://innercircletrader.net/tutorials/ict-market-structure-shift/)
- [MSS meaning & use — fxopen.com](https://fxopen.com/blog/en/market-structure-shift-meaning-and-use-in-ict-trading/)
- [MSS vs BOS — equiti.com](https://www.equiti.com/sc-en/news/trading-ideas/mss-vs-bos-the-ultimate-guide-to-mastering-market-structure/)
- [MSS in SMC/ICT — tradingfinder.com](https://tradingfinder.com/education/forex/ict-mss/)
