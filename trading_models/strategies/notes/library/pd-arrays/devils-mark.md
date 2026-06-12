---
name: devils-mark
aliases: [devil's mark, flat open]
category: pd-arrays
related: [nwog-ndog, consequent-encroachment, true-day-midnight-open]
parameters: {}
detection: not-implemented
---

# Devil's Mark

A candle that opens and immediately moves one way without ever trading to the other
side of its open — leaving a **flat open** (open == high, or open == low, no wick on
one side). The untouched side of the open is "unfinished business": price has never
auctioned on that side of the level, and the level tends to act as a magnet on a
later revisit.

Most commonly tracked on session/daily opens (e.g., a daily candle with no wick above
its open). Terminology note: this is community/ICT-adjacent vocabulary (popularized in
TTrades-style content) rather than a core ICT mentorship term — kept in the library
because the project glossary uses it ("a prior flat open level that acts as a magnet").

## Detection Rules

- On the working timeframe: `open[i] == high[i]` (bearish candle, no upper wick) →
  devil's mark above at `open[i]`; `open[i] == low[i]` → mark below.
- Practical tolerance: within 1 tick (`abs(open - high) <= tick_size`).
- Most useful on H1/H4/daily candles and session opens; register as a magnet level
  with `revisited` flag; clears when price trades through the open from the untouched
  side.

## Sources

- Project glossary: CLAUDE.md (devil's mark)
- Community usage (TTrades / ICT-adjacent); no canonical ICT mentorship source
