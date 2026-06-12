---
name: session-opens
aliases: [session open times, time manipulation, opens]
category: time-theory
related: [ninety-minute-cycles, cycle-order-flow]
ict_refs: [true-day-midnight-open, killzones, judas-swing]
source_coverage: sparse-public   # named in the CM Academy outline; details in paywalled content
parameters:
  candidate_opens_ny: ["12:00 AM (midnight)", "2:30 AM (base cycle)", "7:30/8:30 AM (NY pre/data)", "9:30 AM (equities)", "1:30 PM (PM session)"]
detection: not-implemented
---

# Session Opens & Time Manipulation

A standing CM Academy theme: **session open times are where the algorithm shows its
hand**. The curriculum lists "the importance of session open times" alongside
imbalances and voids, and Kishane's "Time Manipulation" teaching frames the moves
immediately after an open as engineered — the open prints, price runs one way to
collect liquidity, then the session's real delivery begins (the same anatomy as the
ICT Judas swing, told from the time side).

Practical reading, consistent with his cycle framework:

- The open of each session/cycle is a reference price; trading on the wrong side of
  it (relative to your bias) is where the manipulation does its work — and where
  entries are found.
- Moves *into* an open from the prior session tend to be retraced; moves *away* from
  an open with acceptance define the session's flow.
- Detail level is limited in public sources — flesh this file out from his YouTube
  material via `/strategy-from-transcript` (channel: @thecurrencymerchant).

## Detection Rules (provisional)

- Record open prices at each candidate open time (NY-local, DST-safe).
- Features per session: direction of first leg off the open, time and depth of the
  post-open extreme, whether the close confirms opposite-side delivery
  (Judas-day classifier — reuse from the ICT library).
- Bias gate analog: longs below the relevant session open, shorts above, when cycle
  order flow agrees.

## Sources

- [CM Academy outline — coursehero.com](https://www.coursehero.com/file/175168434/Copy-of-CM-Academy-by-Kishane-Robinson-The-Currency-Merchantpdf/)
- [Time Manipulation in Forex — youtube.com/@thecurrencymerchant](https://www.youtube.com/watch?v=1C751wPm25Y)
