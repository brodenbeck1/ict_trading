---
name: three-indians
aliases: [three pushes, three drives, climax reversal, wolfe wave]
category: models
related: [liquidity-sweep-stop-hunt, relative-equal-highs-lows, turtle-soup, smt-divergence, market-structure-shift, swing-points]
parameters:
  pushes: 3
  location_gate: "only valid into a HTF key level (S/R, OB, OTE of a larger leg)"
  wolfe_rules: "pt3 beyond pt1; pt4 back inside the pt1-pt2 range and beyond pt1; pt5 false-breaks the 1-3 trendline"
  target_line: "trendline through points 1 and 4 (the EPA line)"
detection: not-implemented
---

# Three Indians / Wolfe Wave (Climax Reversal)

A **three-push exhaustion reversal**: price drives into a higher-timeframe key level
in three distinct swings, each push printing only a marginal new extreme, and reverses
off the third. The 2020-era notes teach it as the "Three Indians climax reversal"
(three pushes to the high/low), with the **Wolfe wave** as its harmonic skeleton —
typically found inside larger consolidations, channels, and flags near an expected
turn.

ICT-vocabulary reading: pushes 2 and 3 are successive **liquidity raids of the prior
push's extreme** — the third push is the terminal sweep (a
[turtle-soup](turtle-soup.md)-grade false break), which is why the pattern only means
something *at a key level*. Three marginal highs into resistance build the same stop
shelf as [relative-equal-highs-lows](../liquidity/relative-equal-highs-lows.md); SMT
divergence across ES/NQ/YM on the third push is the strongest confirmation.

**Wolfe wave geometry** (bullish case; bearish is the mirror — points label the five
alternating pivots of the final consolidation):

1. Point 3 must be **lower than point 1**;
2. Point 4 must come back **above point 1** and stay within the point 1–2 range;
3. Point 5 most often **false-breaks the trendline drawn through points 1 and 3**
   (the sweep) — and point 3 or 5 sits at the support level;
4. Target: extend the **trendline through points 1 and 4** — price is expected to
   deliver to that line (the take-profit objective).

Figures: `strategies/notes/assets/ict-forex-notes/p098-1.png` (three pushes),
`p099-1.png` (bullish Wolfe), `p100-1.png` (bearish Wolfe).

## Detection Rules

- Pivot labeling: from the confirmed [swing-points](../market-structure/swing-points.md)
  series, find five alternating pivots 1–5 into a marked HTF level where each push
  extreme (1, 3, 5 for bearish-into-resistance) exceeds the prior by only a marginal
  amount (`max_push_extension` in points/ATR — engineered-raid sized, not trend sized).
- Geometry filter (bullish): `low3 < low1`, `high4 > high1`, `high4 <= high2`;
  point 5 trades below the 1–3 trendline value at its bar (the false break).
- Trigger: treat point 5 as the sweep step of the
  [entry-sequence](../entries/entry-sequence.md) — require an MSS with displacement
  back inside before entry (don't fade the third push blindly).
- Confluence upgrades: SMT divergence on push 3; push 3 lands in a HTF PD array;
  shrinking displacement per push (momentum decay).
- Target: the 1–4 line projection at expected delivery time; conservative target =
  opposing side of the consolidation (standard liquidity-to-liquidity exit).
- Stop: beyond the point-5 extreme per
  [stop-placement](../entries/stop-placement.md).

## Sources

- `strategies/notes/ict-forex-notes-mmari-2020.md` §18 (2020 forex-era ICT; primary)
- [Wolfe wave pattern — investopedia.com](https://www.investopedia.com/terms/w/wolfewave.asp)
- [Three drives pattern — babypips.com](https://www.babypips.com/learn/forex/three-drives)
