---
name: daily-bias
aliases: [bias, directional bias]
category: daily-bias
related: [draw-on-liquidity, weekly-profiles, ohlc-candle-profiles, premium-discount, power-of-three]
parameters:
  bias_timeframe: "daily (bias must come from the daily chart, not lower TFs)"
  signals_required: "order flow + imbalance + draw on liquidity must align"
detection: partial   # DailyBiasModel exists in trading_models/sniper/daily_bias_sniper.py
---

# Daily Bias

The expected direction of the current daily candle's expansion — bullish (expected to
expand higher) or bearish (expected to expand lower). The bias frames every intraday
decision: which liquidity pool is the day's target, which side of sweeps to fade, and
which direction entries are allowed.

ICT's bias logic is built on three aligned signals, all read from the **daily** chart:

1. **Order flow** — are recent daily candles delivering higher (bullish) or lower
   (bearish)? Are down-closed candles being respected as support (bullish order flow)
   or up-closed candles as resistance (bearish)?
2. **Imbalance** — is there an unfilled daily FVG / liquidity void above or below that
   price still owes a visit?
3. **Draw on liquidity** — which untaken pool (old high/low, relative equal highs/lows)
   is the nearest magnet? The direction of the next major draw is usually the direction
   of the day. See [draw-on-liquidity](draw-on-liquidity.md).

A common alternation rule: if price just took **internal** range liquidity (filled an
FVG inside the range), the next objective is **external** range liquidity (a range
high/low), and vice versa.

## Detection Rules

- Compute on the daily timeframe at (or before) the session open; hold fixed for the day.
- Bullish bias requires ALL of:
  - daily close > prior daily close structure delivering higher (or respected discount array), AND
  - nearest unmitigated draw (old high / equal highs / unfilled FVG) is ABOVE current price, AND
  - price is trading from a discount relative to the active dealing range.
- Mirror for bearish. If signals conflict → bias = neutral → no trade (rule of exclusion).
- Expect the day to sweep the *nearer, opposing* pool first (manipulation) before
  expanding toward the draw — see [power-of-three](power-of-three.md).

## Sources

- [What is ICT Daily Bias — innercircletraders.net](https://innercircletraders.net/ict-daily-bias/)
- [ICT Daily Bias Explained — innercircletrader.net](https://innercircletrader.net/tutorials/ict-daily-bias-explained/)
- [Daily Bias: Identifying Market Direction — tradingfinder.com](https://tradingfinder.com/education/forex/ict-daily-bias/)
- [ICT Daily Bias mechanical framework — ttrades.com](https://ttrades.com/ict-daily-bias-most-simple-mechanical-framework/)
