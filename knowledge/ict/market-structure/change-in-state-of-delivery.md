---
name: change-in-state-of-delivery
aliases: [CISD, change in the state of delivery]
category: market-structure
related: [market-structure-shift, displacement, order-block, daily-bias]
parameters:
  reference: "opening price(s) of the candle(s) that made the final manipulation leg"
detection: not-implemented
---

# Change in State of Delivery (CISD)

A finer-grained reversal confirmation than the MSS, popular in later ICT teaching and
the TTrades-style mechanical frameworks. Delivery "state" = whether candles are being
delivered bearish (sell-side delivery) or bullish (buy-side delivery).

A **bullish CISD**: after a down-leg sweeps liquidity, price closes **above the opening
price of the consecutive down-closed candles** that made that final low. Reclaiming
those opens means the sell-side delivery failed — the state has changed to buy-side.
Mirror for bearish. CISD often triggers a few bars *earlier* than a full MSS (which
needs a swing break), so some models use CISD as the entry trigger and MSS as added
confirmation.

## Detection Rules

- Identify the manipulation leg into the sweep: the series of consecutive same-color
  candles ending at the extreme.
- Reference level = open of the first candle in that consecutive series (or the chain
  of opens; strictest = highest open of the series for bullish CISD).
- Bullish CISD: `close[t] > reference_open` after the sweep low is in place.
- Emit {time, reference_open, sweep_ref, direction}; the candle series' origin also
  defines the order block zone for re-entry.

## Sources

- [MMXM smart money reversal components (CISD) — tradingview.com](https://www.tradingview.com/script/4eQPT3aC-MMXM-ICT-TradingFinder-Market-Maker-Model-PO3-CHoCH-CSID-FVG/)
- [Change in state of delivery — opofinance.com](https://blog.opofinance.com/en/ict-change-in-state-of-delivery/)
- [TTrades daily bias framework — ttrades.com](https://ttrades.com/ict-daily-bias-most-simple-mechanical-framework/)
