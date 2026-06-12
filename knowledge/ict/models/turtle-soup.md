---
name: turtle-soup
aliases: [turtle soup, false breakout model, sweep reversal]
category: models
related: [liquidity-sweep-stop-hunt, relative-equal-highs-lows, market-structure-shift, smt-divergence]
parameters:
  pool_timeframe: "mark pools on HTF (15m-daily); execute the reversal on LTF"
  stop: "beyond the sweep wick + small buffer"
detection: not-implemented
---

# Turtle Soup

The **failed-breakout reversal model** — ICT's adaptation of the old Connors/Raschke
"Turtle Soup" (fading the turtles' 20-day breakout). In ICT terms it is the purest
liquidity-raid trade:

- **Bearish**: price pokes above a marked swing high / equal highs / 20-day-type
  extreme, takes the buy-side liquidity, fails to accept, and reverses back inside
  the range → short.
- **Bullish**: mirror at a marked low — sweep of sell-side, reversal back inside →
  long.

Sequence: mark the HTF pool → wait for the sweep → require the **LTF market structure
shift** opposite the sweep (don't catch the wick blindly) → enter on the retrace
(FVG/OB of the shift leg or the re-entry into range) → stop beyond the sweep wick →
target the opposing pool of the range.

Relationship to other entries: Turtle Soup *is* steps 2–3 of the canonical sequence
promoted to a named model; the Unicorn and 2022 model usually begin with a turtle-soup
event.

## Detection Rules

- Pool set: prior day/week H/L, equal H/L clusters, session extremes, 20-day extremes.
- Sweep with rejection (close back inside within `rejection_window_bars`).
- Confirmation gate: LTF MSS within N bars of the sweep.
- Entry/stop/target per standard conventions; classify failures where price re-breaks
  the swept level (those are runs — useful filter research).

## Sources

- [ICT turtle soup — innercircletrader.net](https://innercircletrader.net/tutorials/ict-turtle-soup-pattern/)
- [Turtle soup explained — fxopen.com](https://fxopen.com/blog/en/what-is-ict-turtle-soup-and-how-can-you-use-it-in-trading/)
- [Turtle soup identification — fluxcharts.com](https://www.fluxcharts.com/articles/trading-strategies/ict-strategies/ict-turtle-soup)
