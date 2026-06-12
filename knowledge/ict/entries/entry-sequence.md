---
name: entry-sequence
aliases: [entry algorithm, sweep-shift-retrace, confirmation entry]
category: entries
related: [liquidity-sweep-stop-hunt, market-structure-shift, displacement, fair-value-gap, optimal-trade-entry, killzones]
parameters:
  sequence: "context -> sweep -> MSS w/ displacement -> retrace into PD array -> deliver to draw"
  max_bars_sweep_to_mss: "e.g., 30 bars on 1-5m (tunable)"
detection: not-implemented
---

# The Canonical Entry Sequence

Nearly every ICT model is the same five-step state machine wearing different clothes:

1. **Context** — HTF bias set, draw on liquidity identified, price in the correct half
   of the range (discount for longs, premium for shorts), inside an allowed killzone.
2. **Sweep** — a liquidity pool opposing the bias is raided (the manipulation).
3. **Shift** — market structure shift with displacement in the bias direction,
   leaving a PD array (FVG, OB, breaker).
4. **Retrace** — price returns into that PD array; the limit entry fills there
   (gap edge, CE, OB mean threshold, or OTE level).
5. **Delivery** — price runs to the draw; exits per
   [targets-and-exits](targets-and-exits.md).

Rule of exclusion: each step is a gate — any missing step means no trade. Models
differ mainly in *which* pool (step 2), *which* array (step 4), and *which* time
window (step 1) they accept.

## Detection Rules

- Implement as an explicit state machine per instrument-day:
  `IDLE → CONTEXT_OK → SWEPT → SHIFTED → ORDER_PLACED → IN_TRADE → DONE`.
- Transitions carry references: sweep event → MSS event (must break the swing that
  originated the sweep leg) → PD array created by the MSS displacement.
- Timeouts: state resets if MSS doesn't follow the sweep within `max_bars_sweep_to_mss`,
  or the limit isn't filled before the killzone closes / target pool is hit first
  (no chasing — per project decision).

## Sources

- [Complete ICT 2022 strategy — innercircletrader.net](https://innercircletrader.net/tutorials/complete-ict-trading-strategy-2022/)
- [2022 model breakdown — tradingfinder.com](https://tradingfinder.com/education/forex/ict-mentorship-2022-model/)
- Project notes: `strategies/notes/ict-elements-of-a-trade-setup.md`
