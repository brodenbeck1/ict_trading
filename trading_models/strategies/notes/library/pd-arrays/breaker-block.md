---
name: breaker-block
aliases: [breaker, BB, bullish breaker, bearish breaker]
category: pd-arrays
related: [order-block, mitigation-block, liquidity-sweep-stop-hunt, unicorn, inversion-fvg]
parameters:
  required_sequence: "swing -> liquidity sweep of that swing -> displacement back through the originating OB"
detection: not-implemented
---

# Breaker Block

A **failed order block that flips polarity** — the reversal-trade trigger of the block
family. Bullish breaker formation:

1. Price makes a swing low, rallies to a swing high, then **sweeps below the swing low**
   (sell stops taken — this sweep is mandatory);
2. Price reverses and **displaces up through the swing high**, breaking structure;
3. The **last down-closed candle(s) before that up-move** — the order block that failed
   to hold as resistance — is now the *bullish breaker*;
4. Entry: retest of the breaker from above; it should now act as support.

Mirror for bearish breakers. The key discriminator vs. a
[mitigation-block](mitigation-block.md): the breaker sequence includes a **liquidity
raid** (higher high / lower low beyond the prior swing) before the reversal; the
mitigation block does not. No sweep → not a breaker.

## Detection Rules

- Pattern query on swing series (bullish case): swings L1 < H1, then sweep low
  L2 < L1, then displacement close above H1.
- Breaker zone = body of the last down-closed candle (or candle series) between H1 and
  L2 that price broke through during the displacement.
- Entry: first retrace into zone after the structure break; stop below L2 (or below
  breaker zone — config); invalidation if price closes back below the breaker.
- Confluence upgrade: FVG overlapping the breaker = [Unicorn](../models/unicorn.md).

## Sources

- [ICT breaker block trading — innercircletrader.net](https://innercircletrader.net/tutorials/ict-breaker-block-trading/)
- [Breaker & mitigation blocks — tradingview.com](https://www.tradingview.com/chart/GBPCAD/3M3OxgVu-ICT-Breaker-Mitigation-Blocks-EXPLAINED/)
- [Order/breaker/mitigation blocks — theicttrader.com](https://theicttrader.com/2024/03/24/order-blocks-breaker-blocks-and-mitigation-blocks/)
