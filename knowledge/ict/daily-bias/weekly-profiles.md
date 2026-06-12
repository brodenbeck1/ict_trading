---
name: weekly-profiles
aliases: [weekly range profiles, weekly templates]
category: daily-bias
related: [daily-bias, power-of-three, ohlc-candle-profiles, judas-swing]
parameters:
  classic_bullish_template: "low of the week forms Mon/Tue (often Tue London), expansion Tue-Thu"
  expansion_window: "Tuesday ~4:00 AM NY is the classic weekly-expansion anchor"
detection: not-implemented
---

# Weekly Profiles

Templates for how the weekly candle's high and low tend to form day by day. ICT teaches
roughly 12 named profiles (e.g., *Classic Tuesday Low of the Week*, *Wednesday Low*,
*Consolidation Thursday Reversal*, *Seek & Destroy*). The trader's job is not to predict
the profile in advance but to recognize which one is unfolding and position with it.

Key tendencies:

- **Bullish week**: Monday consolidates or manipulates lower; Tuesday (often in London)
  drops into a higher-timeframe discount array and forms the **low of the week**;
  Tuesday–Thursday delivers the expansion; Friday is often profit-taking/consolidation.
- **Bearish week**: mirror image — Mon/Tue manipulation higher into a premium array
  forms the high of the week, then expansion lower.
- **Seek & Destroy**: no clear draw → whipsaw both sides of the opening range; the
  profile to stand aside on.
- Seasonal tendencies (time-of-year directional drift) modulate which profile is more
  probable but never override structure/liquidity evidence.
- Quantified claim (2020 forex-era notes): the weekly high or low forms **~80% of the
  time between the Sunday/Monday open and Tuesday's London open**; when it fails, the
  fallback window is Tuesday's → Wednesday's London open. Testable on ES/NQ/YM —
  classify weekly-extreme timing in backtests before trusting the 80%.

## Detection Rules

- Anchor: weekly open (Sunday 6:00 PM NY) and Monday's range.
- Classify retrospectively for backtests: day-of-week of weekly high and weekly low →
  profile label; use as a feature, not a signal.
- Prospective use: if weekly bias is bullish and Mon/Tue trades below the weekly open
  into a discount array, treat it as candidate manipulation → expect low of week.
- Quantifiable filter: only treat Tue London sweep as "low of the week" candidate if it
  takes a discrete pool (Monday low, Asia low, previous week low).

## Sources

- [ICT Weekly Profiles — 12 patterns — innercircletrader.net](https://innercircletrader.net/tutorials/ict-weekly-range-profiles/)
- [ICT Weekly Range Expansion — innercircletrader.net](https://innercircletrader.net/tutorials/ict-weekly-range-expansion/)
- [Weekly profiles guide — arongroups.co](https://arongroups.co/technical-analyze/ict-weekly-profiles/)
- [Macro narrative: weekly profiles & monthly expansion — fxnx.com](https://fxnx.com/en/blog/ict-macro-narrative-weekly-profiles-monthly-expansion)
- 80% weekly-extreme timing claim: `strategies/notes/ict-forex-notes-mmari-2020.md` §20
