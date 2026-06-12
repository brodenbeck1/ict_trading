---
name: ipda-lookbacks
aliases: [IPDA, IPDA data ranges, 20-40-60 day lookback]
category: daily-bias
related: [draw-on-liquidity, dealing-range, premium-discount]
parameters:
  lookback_days: [20, 40, 60]
  units: "trading days (exclude weekends/holidays)"
detection: not-implemented
---

# IPDA Lookbacks (20 / 40 / 60 Day Ranges)

IPDA — the **Interbank Price Delivery Algorithm** — is ICT's name for the algorithmic
engine he asserts delivers price between pools of liquidity and imbalances. Whatever
one believes about the mechanism, the practical artifact is the **IPDA data ranges**:
the highest high, lowest low, and equilibrium of the past **20, 40, and 60 trading
days**. These define the institutional dealing ranges that frame:

- which old highs/lows are "live" liquidity objectives,
- premium vs. discount at the macro scale,
- which PD arrays (FVGs, order blocks) inside those ranges are still relevant.

The 20-day range is the primary monthly dealing range; 40 and 60 extend the context.
ICT's quarterly-shift idea: every 3–4 months the algorithm re-prices to a new range,
and lookbacks roll forward each day.

## Detection Rules

- For each trading day `t`: `high_n = max(high[t-n:t])`, `low_n = min(low[t-n:t])`,
  `eq_n = (high_n + low_n) / 2` for n in {20, 40, 60}.
- Tag the day: price above `eq_20` = macro premium; below = macro discount.
- Liquidity objectives: untaken `high_20`/`low_20` are first-class draw candidates;
  a 20-day extreme that is also the 40/60-day extreme is a stronger draw.
- Use as regime filter in backtests (e.g., only allow longs when price is in 20-day
  discount and bias is bullish).

## Sources

- [ICT IPDA — 20/40/60-day cycles — innercircletrader.net](https://innercircletrader.net/tutorials/ict-ipda/)
- [IPDA framing of liquidity & imbalance — arongroups.co](https://arongroups.co/technical-analyze/understanding-how-ipda-frames-liquidity-imbalance-and-institutional-price-delivery/)
- [ICT IPDA Look Back indicator — tradingview.com](https://www.tradingview.com/script/rTJEJb5v-ICT-IPDA-Look-Back/)
