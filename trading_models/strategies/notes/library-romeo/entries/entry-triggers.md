---
name: entry-triggers
aliases: [LTF confirmation, CSD entry, CRT entry]
category: entries
related: [purge, fractal-timeframe-pairing, stops-invalidation, targets]
ict_refs: [change-in-state-of-delivery, market-structure-shift, entry-sequence]
parameters:
  confirmation_options: ["CISD/CSD on entry tf (preferred)", "MSS/CHoCH on entry tf", "aggressive: purge wick close-back-inside, no LTF confirmation"]
  entry_price_options: ["on CISD close", "retrace to purge wick / wick CE", "retrace to entry-tf FVG/OB of the confirmation leg"]
detection: not-implemented
---

# Entry Triggers

CRT entries happen on the **entry timeframe** of the pair (4H range → 15m entry)
after the purge, in three escalating styles:

1. **Aggressive** — enter when the purge candle closes back inside the range; no LTF
   confirmation. Best price, most false positives.
2. **Standard (taught default)** — after the purge, wait on the entry tf for a
   **CISD/CSD**: price closing back through the opens of the candles that delivered
   the purge (identical to the ICT
   [change-in-state-of-delivery](../../library/market-structure/change-in-state-of-delivery.md)).
   Enter on the CISD close or the first retrace into the confirmation leg's FVG/OB.
3. **Conservative** — require a full MSS on the entry tf, enter on the retrace into
   the displacement array.

In all styles the trade direction is *away* from the purged side (purge low → long).
A documented refinement: entries near the 50% of the manipulation (purge) candle —
functionally the purge-wick CE described in [wick-ce](../ranges/wick-ce.md).

## Detection Rules

- Subscribe entry-tf bars from `purge_time` forward, max window W bars (config).
- CISD trigger per the ICT-library detection rules, applied to the purge leg's
  consecutive candles.
- Entry order: market on trigger close, or limit at {wick CE | confirmation-leg FVG}
  — config enum matching the three styles.
- Cancel if: opposing extreme purges first, range-tf candle closes beyond the purged
  extreme (failed purge), or W expires.

## Sources

- [CRT entry triggers — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
- [CRT entries & confirmation — writofinance.com](https://www.writofinance.com/candle-range-theory-crt/)
- [CRT + turtle soup CSD — scribd.com](https://www.scribd.com/document/846803727/Basic-of-CRT)
