# Analysis

Post-backtest research documents — one file per study, organized by concept (mirroring `knowledge/`).

---

## File naming

```
analysis/{concept}/{model}-{concept}-{YYYY-MM-DD}.md
```

Examples:
```
analysis/daily-bias/model-2022-daily-bias-2026-06-13.md
analysis/entries/model-2022-fvg-entry-2026-07-01.md
analysis/killzones/model-2022-killzone-timing-2026-07-15.md
```

- **`{concept}`** — matches a folder name under `knowledge/ict/` (e.g. `daily-bias`, `entries`, `killzones`, `pd-arrays`)
- **`{model}`** — the model being studied (e.g. `model-2022`, `romeo-crt`)
- **`{YYYY-MM-DD}`** — date the analysis was run, not the backtest date range

If a study spans multiple concepts, use the concept that is the primary focus.

---

## Required sections

Every analysis document must include:

```markdown
# {Model} — {Concept} Study

**Model**: model-name
**Concept**: concept-slug
**Instrument**: NQ | ES | YM | multi
**Analysis date**: YYYY-MM-DD
**Dataset**: description of date range and bar count
**Scripts**: scripts that produced the results
**Raw results**: paths to CSV outputs in results/
**Configs**: paths to YAML configs used (if any)
```

Then at minimum:
- **What Was Tested** — parameters, gate combos, or config variations
- **Results** — tables, key numbers
- **Key Findings** — numbered, one insight per finding
- **Recommendations** — concrete next actions with priority
- **Open Questions** — things not answered by this study

---

## What belongs here vs elsewhere

| Content | Goes in |
|---|---|
| Concept definitions, detection rules, ICT semantics | `knowledge/` |
| Human strategy write-ups from video transcripts | `strategies/notes/` |
| Backtest runner scripts | `backtests/` |
| Named experiment configs | `configs/{model}/` |
| Raw trade logs and equity curves | `results/` (gitignored) |
| **Quantitative findings from backtests** | **`analysis/`** ← here |
| Parameter grid search results and interpretation | `analysis/` |
| Session/killzone breakdowns | `analysis/` |
| Recommendations for model changes based on data | `analysis/` |

---

## Updating existing documents

Do not edit an existing analysis file to reflect new results. Instead, create a new file with the current date. The old file is a historical record of what was known at that point. Link between files using relative markdown links when a new study supersedes or extends an old one:

```markdown
*Supersedes: [model-2022-daily-bias-2026-06-13.md](model-2022-daily-bias-2026-06-13.md)*
```

---

## Index

| File | Model | Concept | Date | Summary |
|---|---|---|---|---|
| [model-2022-daily-bias-2026-06-13.md](daily-bias/model-2022-daily-bias-2026-06-13.md) | model-2022 | daily-bias | 2026-06-13 | Grid search across 12 gate combos; hard 4H gate best; London 0 trades; NY AM longs 0-for-7; 10-13:30 UTC window untapped |
| [currency-merchant-dxy-weekly-bias-plan-2026-06-14.md](dxy-weekly-bias/currency-merchant-dxy-weekly-bias-plan-2026-06-14.md) | currency-merchant | dxy-weekly-bias | 2026-06-14 | Build plan: weekly DXY pool reaction (MSS/CISD) → NQ weekly bias; in-progress |
