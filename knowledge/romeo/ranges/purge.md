---
name: purge
aliases: [sweep, raid, liquidation, wick of the range]
category: ranges
related: [crt-range, inside-bars-accumulation, entry-triggers, timing-protocol]
ict_refs: [liquidity-sweep-stop-hunt, turtle-soup]
parameters:
  purge_rule: "trade beyond crt.high/low followed by close back inside the range"
  failed_purge: "close beyond the range = breakout/continuation, not a purge"
detection: not-implemented
---

# The Purge

The defining CRT event: price **wicks beyond one extreme of the range and closes back
inside**. The stops beyond that extreme are "purged" — collected as counterparty
liquidity — and the candle that did it telegraphs intent toward the *opposite* side
of the range.

Rules of interpretation:

- **Purge low → bullish bias** toward the range 50%, then the range high.
- **Purge high → bearish bias** toward the 50%, then the low.
- **Close beyond the extreme = not a purge.** Acceptance outside the range is a
  breakout/expansion — CRT offers no fade there. The close back inside is what makes
  it manipulation. (Identical logic to the ICT sweep-vs-run distinction.)
- One side purging then the other ("double purge") resets the read — typically a
  Seek & Destroy-type condition; stand aside.
- High-quality purges happen at key times — grade by
  [timing-protocol](../protocols/timing-protocol.md); a purge into a coupled HTF key
  level ([key-level-coupling](../protocols/key-level-coupling.md)) is the A+ form.

## Detection Rules

- On range-tf candle t: `purged_low if low[t] < crt.low and close[t] > crt.low`
  (mirror for high). Intrabar variant on entry-tf for earlier detection.
- Disqualify: `close[t] < crt.low` → mark CRT `broken` (no trade).
- Record purge features: depth beyond extreme (points & % of range height), NY-local
  time, killzone membership, coupled key level hit (bool), LTF confirmation
  (CISD/MSS) reference.
- Double-purge flag if both extremes wicked within the same resolution window.

## Sources

- [CRT purge rules — tradingwyckoff.com](https://tradingwyckoff.com/en/crt/)
- [Mastering CRT — scribd.com](https://www.scribd.com/document/898327293/Crt)
- [CRT golden rule — writofinance.com](https://www.writofinance.com/candle-range-theory-crt/)
