---
name: displacement
aliases: [energetic move, institutional sponsorship]
category: market-structure
related: [fair-value-gap, market-structure-shift, liquidity-void, change-in-state-of-delivery]
parameters:
  body_atr_mult: "candle/leg body >= k * ATR(14), e.g., k = 1.5-2.0 (tunable)"
  must_leave_fvg: "strongest form of displacement leaves at least one FVG"
detection: not-implemented
---

# Displacement

An aggressive, one-sided price expansion — large-bodied candles, minimal opposing
wicks, typically leaving fair value gaps behind. Displacement is read as **evidence of
institutional sponsorship**: enough size traded in one direction that price could not
be delivered efficiently.

Roles in the framework:

- Validates a structure break (an MSS without displacement is suspect).
- Creates the PD arrays used for entry (the FVG/order block of the displacement leg).
- After a liquidity sweep, displacement *away* from the swept pool confirms the raid
  is complete and the real move is underway.

## Detection Rules

- Candle-level: `body[t] >= body_atr_mult * ATR(14)` and body/range ratio >= e.g. 0.7.
- Leg-level: net move over n bars >= k * ATR with <= m% retracement inside the leg.
- Boolean upgrade: leg contains at least one FVG → `displacement_with_fvg = true`
  (most models require this form).
- Record direction, start/end price-time, FVGs created, and the swing levels broken.

## Sources

- [MSS & displacement — fxopen.com](https://fxopen.com/blog/en/market-structure-shift-meaning-and-use-in-ict-trading/)
- [MSS displacement definition — writofinance.com](https://www.writofinance.com/ict-market-structure-shift-mss/)
- [Market structure shift 101 — crypoptionhub.com](https://crypoptionhub.com/ict-market-structure-shift/)
