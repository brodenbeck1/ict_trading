# Romeo (CRT) Concept Library

Candle Range Theory as taught by **Romeo (@Romeotpt)** — the "every candle is a
range" framework. Same file schema as the [ICT library](../library/README.md)
(`name`/`aliases`/`category`/`related`/`parameters`/`detection` frontmatter +
Detection Rules + Sources), with one addition: an **`ict_refs:`** frontmatter field
linking each concept to its ICT-library equivalents, since CRT deliberately reuses
ICT primitives (PO3, turtle soup, CISD, CE, PD arrays) under a candle-centric lens.

**Attribution note**: many sites brand CRT as "ICT CRT" because it derives from
ICT's Power of Three and turtle soup; community consensus credits the systematized
theory to @Romeotpt. Sources researched 2026-06-11. Times are NY-local; project data
is UTC — mind the 4H resampling anchor (see timing-protocol).

---

## Index

### core/ — axioms
| Concept | One-liner |
|---|---|
| [candle-range-principle](core/candle-range-principle.md) | Every candle is a range; OHLC anatomy as liquidity story |
| [fractal-timeframe-pairing](core/fractal-timeframe-pairing.md) | D→1H, 4H→15m, 1H→5m range/entry pairs |
| [time-over-price](core/time-over-price.md) | "Time > Price" — when outranks where |

### ranges/ — mechanics
| Concept | One-liner |
|---|---|
| [crt-range](ranges/crt-range.md) | The HTF candle as dealing range; lifecycle state machine |
| [inside-bars-accumulation](ranges/inside-bars-accumulation.md) | More inside bars = more fuel |
| [purge](ranges/purge.md) | Wick beyond + close back inside; close beyond = breakout, no trade |
| [wick-ce](ranges/wick-ce.md) | Wicks as inefficiencies; range/body/wick 50% levels |

### protocols/ — setup grading
| Concept | One-liner |
|---|---|
| [quality-protocols](protocols/quality-protocols.md) | Stacked filters; "+11% per protocol" treated as hypothesis |
| [timing-protocol](protocols/timing-protocol.md) | Key times: 1/5/9 AM, 1/3/9 PM NY; 4H anchor warning |
| [key-level-coupling](protocols/key-level-coupling.md) | Purge into HTF array; RB > OB > FVG > breaker |

### entries/ — execution
| Concept | One-liner |
|---|---|
| [entry-triggers](entries/entry-triggers.md) | Aggressive wick-close / standard CISD / conservative MSS |
| [stops-invalidation](entries/stops-invalidation.md) | Stop beyond purge wick; range-tf close beyond = hard kill |
| [targets](entries/targets.md) | Ladder: range 50% → opposing extreme → beyond |

### models/ — composites
| Model | Essence |
|---|---|
| [three-candle-model](models/three-candle-model.md) | A-M-D in three candles; candle 2 = "the soup" |
| [4h-crt-model](models/4h-crt-model.md) | 1 AM range → 5 AM purge → 9 AM delivery, 15m entries |
| [daily-weekly-crt](models/daily-weekly-crt.md) | PDH/PDL purges & Monday-range weeks as CRTs |

---

## ICT ↔ CRT translation table

| CRT term | ICT equivalent |
|---|---|
| Range (CRT candle) | Dealing range |
| Purge / "the soup" | Liquidity sweep / turtle soup |
| Close back inside rule | Sweep vs. run distinction |
| CSD | CISD (change in state of delivery) |
| Range 50% | Equilibrium |
| Wick CE | Consequent encroachment |
| Inside bars | Accumulation (PO3) |
| Key times | Killzones / macros |
| Key-level coupling | HTF PD array confluence |
| Three-candle model | PO3 / OHLC profile / Judas |

The mapping means most CRT detectors can be thin wrappers over ICT-library
primitives parameterized per-candle — build once, expose under both vocabularies.
