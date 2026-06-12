---
name: judas-swing
aliases: [judas, false move, london trap]
category: models
related: [power-of-three, liquidity-sweep-stop-hunt, ohlc-candle-profiles, killzones, true-day-midnight-open]
parameters:
  classic_window: "London killzone (2-5 AM NY); NY variant: 9:30-10:00 AM after the equity open"
  reference: "midnight open / session opening range"
detection: not-implemented
---

# Judas Swing

The **manipulation leg of the session personified**: the engineered false move shortly
after a session opens, running against the day's true direction to sweep liquidity and
trap traders before the real move. Named for the betrayal — the first directional move
of the session "betrays" those who follow it.

Classic form (bullish day): after the London (or NY) open, price breaks *below* the
opening range / Asia low / midnight open, takes the sell stops, then reverses to spend
the rest of the session rallying. The Judas extreme frequently becomes the **low or
high of the entire day** — which is what makes fading it attractive: entries near the
day's extreme with the whole expansion as the runway.

As a tradable model: bias must be pre-established; the Judas swing is the *sweep step*
of the entry sequence, traded once MSS confirms — not faded blindly.

## Detection Rules

- Reference levels: midnight open, session opening price, Asia range extremes.
- Judas candidate: within the first portion of the killzone (e.g., first 60-90 min),
  price trades beyond a reference level *against* the daily bias, then closes back
  across the reference.
- Confirmation: MSS with displacement back in the bias direction → standard sequence
  resumes.
- Day-label for research: `judas_day = (extreme against bias printed in first kz) AND
  (close in opposite third of range)`.

## Sources

- [Power of 3 / manipulation — innercircletrader.net](https://innercircletrader.net/tutorials/ict-power-of-3/)
- [Judas swing London trap — fxnx.com](https://fxnx.com/en/blog/mastering-ict-judas-swing-gold-trading-london-trap)
- [Daily bias, killzones & judas — tradingstrategyguides.com](https://tradingstrategyguides.com/day-16-how-to-build-an-ict-trade-plan-daily-bias-kill-zones-judas-swing/)
