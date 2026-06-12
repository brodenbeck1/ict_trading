---
name: targets-and-exits
aliases: [take profit, low-hanging fruit, partials]
category: entries
related: [draw-on-liquidity, internal-external-range-liquidity, premium-discount, stop-placement]
parameters:
  primary_target: "nearest opposing liquidity pool / imbalance past the 50% of the governing range"
  min_rr: "2-3R typical gate (2022 model uses minimum 1:3); below threshold -> skip trade"
  partials: "common scheme: scale at first pool, runner to the HTF draw"
detection: not-implemented
---

# Targets & Exits

ICT targeting is liquidity-to-liquidity: the exit is **where the next counterparty
pool sits**, not a fixed R multiple. Operating rules:

1. **Low-hanging fruit first** — the nearest opposing pool or unfilled imbalance is
   the primary objective. Don't aim past it; take what the market offers.
2. **Range logic** — shorts from premium target the first discount array below
   equilibrium; longs from discount target premium arrays. Crossing EQ is the
   minimum expectation for a valid setup.
3. **The HTF draw is the bonus** — trail a runner toward the daily/weekly draw only
   when the move is clearly delivering; never hold the full position for it.
4. **R:R gate** — if (entry − target) / (stop − entry) < min_rr, the setup is skipped
   even if every other box is checked.

Time-based exits matter too: a position still open when the killzone/true day expires
has lost its window — many models flatten at session close rather than hold.

## Detection Rules

- Target = nearest level from the liquidity/PD-array registry in the trade direction,
  filtered to `beyond EQ` of the governing range.
- Compute and log `rr_planned` at signal time; gate on `rr_planned >= min_rr`.
- Exit simulation order on each bar (conservative): stop before target when both are
  inside one bar's range (config: `intrabar_priority = stop_first`).
- Log `exit_reason in {target, stop, eod, kz_close}` per project trade-log schema.

## Sources

- [2022 model (1:3 minimum) — innercircletrader.net](https://innercircletrader.net/tutorials/complete-ict-trading-strategy-2022/)
- [Silver bullet targets — innercircletrader.net](https://innercircletrader.net/tutorials/ict-silver-bullet-strategy/)
- Project notes: `strategies/notes/ict-elements-of-a-trade-setup.md` (low-hanging fruit)
