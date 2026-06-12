---
name: macros
aliases: [ICT macros, macro times, algorithmic macros]
category: time-and-price
related: [killzones, silver-bullet, liquidity-sweep-stop-hunt]
parameters:
  commonly_cited_macros_ny: ["2:33-3:00 AM", "4:03-4:30 AM", "8:50-9:10 AM", "9:50-10:10 AM", "10:50-11:10 AM", "11:50-12:10 PM", "1:10-1:40 PM", "3:15-3:45 PM"]
  core_pair_ny: ["9:45-10:15 AM", "10:45-11:15 AM"]
detection: not-implemented
---

# Macros

Short (20–30 minute) windows in which ICT claims the delivery algorithm runs a
"macro" — a scripted routine that either **runs out a nearby liquidity pool or
rebalances a nearby FVG**, frequently producing the sharp spike-and-reverse moves seen
around :50–:10 of certain hours.

The two most-cited index macros are **9:45–10:15 AM** and **10:45–11:15 AM** NY — note
they bracket the 10–11 AM Silver Bullet window. The fuller community list is in the
parameters block (sources vary slightly on exact minutes).

Practical use is twofold:
1. **Anticipation** — expect acceleration toward the nearest pool/FVG when a macro
   opens; a setup that needs one last sweep often gets it during a macro.
2. **Avoidance** — don't place resting stops just beyond obvious pools right before a
   macro window.

## Detection Rules

- Implement as NY-local time masks (same DST-safe approach as killzones).
- Backtest features per macro window: direction & magnitude of the move, whether a
  registered pool was swept or an FVG filled within the window.
- This is an empirically testable claim — a good early research task is measuring
  whether sweep frequency inside macro windows exceeds matched control windows.

## Sources

- [Killzones + macros indicator — tradingview.com](https://www.tradingview.com/script/3IAWXYpA-ICT-Killzones-Macros-TakingProphets/)
- [ICT killzones and macros — mql5.com](https://www.mql5.com/en/market/product/108297)
- [Killzones & macros — tradingview.com (RuntimeRascal)](https://www.tradingview.com/script/dCwZ85Hs-ICT-Killzones-Macros/)
