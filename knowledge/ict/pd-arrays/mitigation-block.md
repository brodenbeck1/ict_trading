---
name: mitigation-block
aliases: [MB]
category: pd-arrays
related: [order-block, breaker-block]
parameters:
  distinguisher: "no liquidity raid before the reversal (vs breaker, which requires one)"
detection: not-implemented
---

# Mitigation Block

An old order block that price returns to **re-test after the original move played
out**, acting as continuation support/resistance **in the original direction**. The
institutional narrative: orders left underwater at that block are "mitigated"
(exited at break-even-ish) on the retest, and fresh positions are added with the trend.

Family placement — the "block trio":

| Block | Sweep before reversal? | Role |
|---|---|---|
| Breaker | Yes (HH/LL raid) | Reversal trigger |
| Mitigation | No | Continuation re-test |
| Rejection | Wick at swept extreme | Reversal at the wick |

So: if structure broke after a liquidity raid → grade the zone a breaker; if structure
broke without the raid (a plain failure swing) → mitigation block.

## Detection Rules

- Bullish case: swing low L1, rally, pullback that makes a **higher low** (no sweep of
  L1), then displacement up through the prior high.
- Mitigation zone = body of the last down-closed candle(s) in that pullback.
- Entry on first retrace into the zone with trend; stop below the pullback low.
- Registry note: a broken mitigation block (close through far side) is just a dead
  zone — it does not earn breaker status without a raid.

## Sources

- [ICT mitigation block explained — innercircletrader.net](https://innercircletrader.net/tutorials/ict-mitigation-block-explained/)
- [Order/breaker/mitigation blocks — theicttrader.com](https://theicttrader.com/2024/03/24/order-blocks-breaker-blocks-and-mitigation-blocks/)
