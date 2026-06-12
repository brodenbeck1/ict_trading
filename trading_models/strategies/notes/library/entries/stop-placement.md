---
name: stop-placement
aliases: [stop loss, invalidation, protected swing]
category: entries
related: [liquidity-sweep-stop-hunt, entry-sequence, swing-points, order-block]
parameters:
  standard: "beyond the swept extreme (the 'protected' swing) — project decision"
  tight: "beyond the entry PD array (FVG/OB far edge)"
  buffer: "small fixed buffer beyond the level (ticks) to survive equal-extreme retests"
detection: not-implemented
---

# Stop Placement

ICT stops are placed at **structural invalidation**, not at a fixed dollar distance.
The logic: the swept extreme is "protected" — if the model's premise (raid complete,
reversal underway) is true, the algorithm should not revisit it. Options from widest
to tightest:

1. **Beyond the swept swing** (project standard) — the high/low taken in the stop
   hunt. Most robust; survives deep retests.
2. **Beyond the entry array** — far edge of the FVG / order block. Smaller risk,
   higher chance of being wicked out by a deep CE/OTE test.
3. **Beyond the MSS displacement origin** — middle ground.

A revisit of the protected level isn't just a lost trade — it *invalidates the read*
(the sweep was actually a run), so re-entry in the same direction requires the full
sequence to rebuild. Position size derives from stop distance: contracts =
risk_dollars / (stop_points × point_value) — fixed at 1 contract in this project's
backtests.

## Detection Rules

- `stop = swept_extreme ± buffer_ticks` (direction-appropriate).
- Record stop distance in points and as ATR multiple — both are useful normalization
  features in results analysis.
- Exit codes in the trade log: `stop` (structural invalidation) vs `target` vs `eod`
  (time stop at session close, if the model uses one).
- Break-even / trailing rules are model-specific; default backtest = static stop.

## Sources

- [Turtle soup risk management — fxopen.com](https://fxopen.com/blog/en/what-is-ict-turtle-soup-and-how-can-you-use-it-in-trading/)
- [2022 model rules — innercircletrader.net](https://innercircletrader.net/tutorials/complete-ict-trading-strategy-2022/)
- Project decision log: `strategies/notes/ict-elements-of-a-trade-setup.md`
