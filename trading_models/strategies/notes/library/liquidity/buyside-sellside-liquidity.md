---
name: buyside-sellside-liquidity
aliases: [BSL, SSL, buy stops, sell stops]
category: liquidity
related: [liquidity-pools, relative-equal-highs-lows, liquidity-sweep-stop-hunt, draw-on-liquidity]
parameters: {}
detection: not-implemented
---

# Buy-Side & Sell-Side Liquidity (BSL / SSL)

Liquidity in the ICT sense = resting orders that smart money can fill against.

- **Buy-side liquidity (BSL)** sits **above** old highs and relative equal highs: the
  buy stops of shorts plus breakout-buy entries. When price runs through the high, those
  orders execute — providing the buying that institutions sell into.
- **Sell-side liquidity (SSL)** sits **below** old lows and relative equal lows: the
  sell stops of longs plus breakout-sell entries — the selling institutions buy from.

Core mechanic of the whole framework: price is delivered **to** liquidity, not away
from it. Significant moves begin by sweeping the opposing pool (creating counterparties)
and end by reaching the target pool.

## Detection Rules

- Every confirmed swing high carries a BSL tag at `swing.high`; every swing low an SSL
  tag at `swing.low` (see [swing-points](../market-structure/swing-points.md)).
- Pool weight increases with: number of equal touches, age, timeframe of the swing,
  and confluence with session levels (PDH/PDL, Asia/London H/L).
- A pool is consumed when price trades through it; record sweep time and whether price
  closed beyond (run) or rejected (sweep) — see
  [liquidity-sweep-stop-hunt](liquidity-sweep-stop-hunt.md).

## Sources

- [Buy-side vs sell-side liquidity — innercircletrader.net](https://innercircletrader.net/tutorials/liquidity-in-forex-trading/)
- [BSL & SSL guide — tradingfinder.com](https://tradingfinder.com/education/forex/ict-bsl-ssl/)
- [Buy/sell side liquidity — writofinance.com](https://www.writofinance.com/buy-side-and-sell-side-liquidity-ict-and-smc/)
- [Liquidity in ICT — arongroups.co](https://arongroups.co/technical-analyze/liquidity-in-ict/)
