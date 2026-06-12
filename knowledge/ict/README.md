# ICT Concept Library

A semantic layer for the ICT framework: one file per concept, written to be read by
humans *and* parsed by tooling. Models in `trading_models/` should reference these
slugs in their docstrings/configs so every backtest rule traces back to a definition.

**Format** — every file has YAML frontmatter:

```yaml
name: kebab-case-slug        # unique ID, matches filename
aliases: [FVG, imbalance]    # search terms / abbreviations
category: pd-arrays          # matches the folder
related: [other-slugs]       # graph edges
parameters: {...}            # quantifiable knobs with defaults/decisions
detection: not-implemented   # not-implemented | partial | implemented
```

Body sections: prose definition → **Detection Rules** (quantifiable, backtest-ready
logic) → **Sources** (URLs researched 2026-06-11; project decisions cite
`strategies/notes/ict-elements-of-a-trade-setup.md`).

**Time convention**: ICT times are quoted in **New York local time** (the canonical
reference); the project's CSV data is **UTC**. Always convert via `America/New_York`
per-date — never hardcode UTC offsets (DST: EDT = UTC−4, EST = UTC−5).

---

## Index

### daily-bias/ — which way, and toward what
| Concept | One-liner |
|---|---|
| [daily-bias](daily-bias/daily-bias.md) | Expected direction of the daily candle; order flow + imbalance + DOL |
| [draw-on-liquidity](daily-bias/draw-on-liquidity.md) | The level price is magnetized toward (DOL) |
| [power-of-three](daily-bias/power-of-three.md) | Accumulation → Manipulation → Distribution (PO3/AMD) |
| [ohlc-candle-profiles](daily-bias/ohlc-candle-profiles.md) | OHLC = bearish day, OLHC = bullish day; trade the right side of the open |
| [weekly-profiles](daily-bias/weekly-profiles.md) | 12 templates for when the weekly high/low forms (Tuesday low etc.) |
| [ipda-lookbacks](daily-bias/ipda-lookbacks.md) | 20/40/60-day ranges framing institutional dealing |

### liquidity/ — the fuel
| Concept | One-liner |
|---|---|
| [buyside-sellside-liquidity](liquidity/buyside-sellside-liquidity.md) | BSL above highs, SSL below lows — resting stops |
| [liquidity-pools](liquidity/liquidity-pools.md) | PDH/PDL, Asia/London/NY session extremes |
| [relative-equal-highs-lows](liquidity/relative-equal-highs-lows.md) | Engineered stop shelves (EQH/EQL); tolerance = 20 NQ pts start |
| [liquidity-sweep-stop-hunt](liquidity/liquidity-sweep-stop-hunt.md) | Raid + rejection vs. run + acceptance |
| [inducement](liquidity/inducement.md) | Engineering the pools / trapping entries in front of the real array |
| [internal-external-range-liquidity](liquidity/internal-external-range-liquidity.md) | ERL ↔ IRL alternation — the standing answer to "what's next" |
| [liquidity-void](liquidity/liquidity-void.md) | Multi-candle one-sided imbalance corridor |

### market-structure/ — the skeleton
| Concept | One-liner |
|---|---|
| [swing-points](market-structure/swing-points.md) | 3-bar pivots; ST/IT/LT hierarchy *(implemented: SwingPointScanner)* |
| [break-of-structure](market-structure/break-of-structure.md) | With-trend swing break = continuation (BOS/BMS) |
| [market-structure-shift](market-structure/market-structure-shift.md) | Counter-trend break **with displacement** = reversal (MSS/CHoCH) |
| [displacement](market-structure/displacement.md) | Energetic one-sided expansion; institutional sponsorship |
| [change-in-state-of-delivery](market-structure/change-in-state-of-delivery.md) | CISD — reclaiming the manipulation candles' opens |
| [dealing-range](market-structure/dealing-range.md) | Swing-to-swing container; the measuring stick |

### pd-arrays/ — the reaction zones
| Concept | One-liner |
|---|---|
| [pd-array-matrix](pd-arrays/pd-array-matrix.md) | The ordered checklist of premium/discount arrays |
| [premium-discount](pd-arrays/premium-discount.md) | EQ = 50%; never buy premium, never sell discount |
| [fair-value-gap](pd-arrays/fair-value-gap.md) | 3-candle imbalance (BISI/SIBI); the workhorse entry array |
| [inversion-fvg](pd-arrays/inversion-fvg.md) | Failed FVG flips polarity (IFVG) |
| [balanced-price-range](pd-arrays/balanced-price-range.md) | Overlap of opposing FVGs (BPR) |
| [volume-imbalance](pd-arrays/volume-imbalance.md) | Body gap with wick overlap — thin inefficiency |
| [order-block](pd-arrays/order-block.md) | Last opposing candle before displacement |
| [breaker-block](pd-arrays/breaker-block.md) | Failed OB after a raid — polarity flip, reversal trigger |
| [mitigation-block](pd-arrays/mitigation-block.md) | OB retest without a raid — continuation |
| [rejection-block](pd-arrays/rejection-block.md) | The wick of the sweep candle as the zone |
| [nwog-ndog](pd-arrays/nwog-ndog.md) | Weekend / maintenance-hour true gaps (keep last 5 NWOGs) |
| [consequent-encroachment](pd-arrays/consequent-encroachment.md) | CE — the 50% of any gap or wick |
| [devils-mark](pd-arrays/devils-mark.md) | Flat-open candle; the untouched open as magnet |

### time-and-price/ — when
| Concept | One-liner |
|---|---|
| [killzones](time-and-price/killzones.md) | London 2–5 AM, NY AM 8:30–11, etc. (NY time) — time gates price |
| [sessions-and-ranges](time-and-price/sessions-and-ranges.md) | Asia range, CBDR, flout, SD projections |
| [macros](time-and-price/macros.md) | 20–30 min algorithmic run/rebalance windows |
| [true-day-midnight-open](time-and-price/true-day-midnight-open.md) | Midnight NY open; true day = 00:00–15:00 NY |

### entries/ — execution mechanics
| Concept | One-liner |
|---|---|
| [entry-sequence](entries/entry-sequence.md) | Context → sweep → shift → retrace → deliver (the universal state machine) |
| [optimal-trade-entry](entries/optimal-trade-entry.md) | OTE: 62–79% retracement, 70.5% sweet spot |
| [smt-divergence](entries/smt-divergence.md) | Correlation crack across ES/NQ/YM — confirmation layer |
| [stop-placement](entries/stop-placement.md) | Structural invalidation beyond the protected (swept) swing |
| [targets-and-exits](entries/targets-and-exits.md) | Liquidity-to-liquidity; low-hanging fruit first; R:R gate |

### models/ — named composites
| Model | Essence |
|---|---|
| [model-2022](models/model-2022.md) | Bias + sweep + MSS + FVG entry, 1:3 minimum — the canonical intraday model |
| [silver-bullet](models/silver-bullet.md) | FVG trade strictly inside 3–4 AM / 10–11 AM / 2–3 PM NY |
| [unicorn](models/unicorn.md) | Breaker ∩ FVG overlap zone |
| [turtle-soup](models/turtle-soup.md) | Failed breakout / sweep-reversal at a marked pool |
| [judas-swing](models/judas-swing.md) | Fading the session-open false move |
| [market-maker-models](models/market-maker-models.md) | MMBM/MMSM full delivery curve; left side = right side's target ladder |
| [one-shot-one-kill](models/one-shot-one-kill.md) | One weekly-range trade, Mon–Wed anchor, OTE entry |

---

## Alias lookup

| Abbreviation | Concept |
|---|---|
| AMD, PO3 | power-of-three |
| BISI / SIBI | fair-value-gap |
| BOS, BMS | break-of-structure |
| BPR | balanced-price-range |
| BSL / SSL | buyside-sellside-liquidity |
| CBDR | sessions-and-ranges |
| CE | consequent-encroachment |
| CHoCH | market-structure-shift |
| CISD | change-in-state-of-delivery |
| DOL | draw-on-liquidity |
| EQ | premium-discount |
| EQH / EQL, REH / REL | relative-equal-highs-lows |
| ERL / IRL | internal-external-range-liquidity |
| FVG | fair-value-gap |
| IDM | inducement |
| IFVG | inversion-fvg |
| IPDA | ipda-lookbacks |
| KZ | killzones |
| MMXM / MMBM / MMSM | market-maker-models |
| MSS | market-structure-shift |
| NWOG / NDOG | nwog-ndog |
| OB | order-block |
| OSOK | one-shot-one-kill |
| OTE | optimal-trade-entry |
| PDH / PDL | liquidity-pools |
| SB | silver-bullet |
| SMT | smt-divergence |
| STH/STL, ITH/ITL, LTH/LTL | swing-points |
| VI | volume-imbalance |

## Using this as a semantic layer

- **Parsing**: every file's frontmatter is loadable with `yaml.safe_load` on the block
  between the `---` fences; `name`/`category`/`related` give you the concept graph.
- **Detection status**: grep `detection:` to see what's coded vs. pending. Update the
  flag (and add a `Project code:` line under Sources) when a detector lands in
  `ict_library`.
- **Building a model**: pick a file in `models/`, pull its `related` closure, and the
  union of those Detection Rules sections is the spec.
