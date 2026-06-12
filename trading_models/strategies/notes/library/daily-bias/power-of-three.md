---
name: power-of-three
aliases: [PO3, AMD, accumulation-manipulation-distribution]
category: daily-bias
related: [judas-swing, ohlc-candle-profiles, weekly-profiles, killzones, liquidity-sweep-stop-hunt]
parameters:
  accumulation_window: "Asia session / pre-London consolidation"
  manipulation_window: "London killzone 2:00-5:00 AM NY (or NY pre-market for index-only days)"
  distribution_window: "NY session 8:30 AM onward"
detection: not-implemented
---

# Power of Three (PO3 / AMD)

The fractal template for how any candle (daily, weekly, session) is built in three
phases:

1. **Accumulation** — price consolidates in a tight range around the open while
   institutions build positions. Liquidity forms on both sides of the range.
2. **Manipulation** — an engineered run *against* the day's true direction that sweeps
   one side of the range (the [Judas swing](../models/judas-swing.md)). Bullish day →
   sell-side is swept below the range; bearish day → buy-side swept above.
3. **Distribution** — the real expansion in the institutional direction, delivering to
   the draw on liquidity, with the close near that extreme.

The sweep direction during manipulation is the tell: **BSL swept → expect bearish
distribution; SSL swept → expect bullish distribution** (conditional on HTF bias
agreeing).

## Detection Rules

- Define the accumulation range: e.g., Asia range (18:00–00:00 UTC per project
  convention) or the 00:00–02:00 NY opening range.
- Manipulation detected when price trades beyond one side of the accumulation range and
  closes back inside within N bars (parameter, e.g., N=12 on 5m), during the
  London/NY-AM killzone.
- Distribution confirmation: market structure shift with displacement in the opposite
  direction of the manipulation sweep.
- Backtest label: day exhibits PO3 if `range_breakout_first_side != side_of_close` and
  close is in the outer third of the day's range.

## Sources

- [ICT Power of 3 — innercircletrader.net](https://innercircletrader.net/tutorials/ict-power-of-3/)
- [ICT PO3 — fxopen.com](https://fxopen.com/blog/en/what-is-ict-po3-and-how-do-traders-use-it/)
- [PO3 three phases — tradingfinder.com](https://tradingfinder.com/education/forex/ict-power-of-three/)
- [What is ICT Power of 3 — arongroups.co](https://arongroups.co/technical-analyze/power-of-3/)
