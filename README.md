# ICT Trading Research

Futures trading research project implementing ICT (Inner Circle Trader) concepts on ES, NQ, and YM continuous contracts.

## What's in here

| Layer | Location | Purpose |
|---|---|---|
| **Knowledge base** | `knowledge/ict/` | One markdown file per ICT concept with YAML frontmatter — the semantic layer |
| **Package** | `src/ict/` | Installable Python package: data loader, concept detectors, trading models |
| **Backtests** | `backtests/` | Runner scripts; outputs land in `results/` (gitignored) |
| **Strategy notes** | `strategies/notes/` | Human write-ups extracted from video/PDF sources |
| **Data** | `Data/` | 1m continuous contracts for ES, NQ, YM (~1.1 GB, gitignored) |

## Setup

```bash
pip install -e .
```

Data files are not in the repo. Run the acquisition pipeline in `Data/prep/` with a Databento API key.

## Quick start

```python
from ict import DataLoader

loader = DataLoader(timeframe='5T', weeks=52, data_dir='Data')
nq = loader.read_NQ()   # returns DataFrame with DatetimeIndex
es = loader.read_ES()
ym = loader.read_YM()
```

Timeframes: `'1T'` `'5T'` `'15T'` `'1H'` `'4H'` `'D'`

## Running a backtest

```bash
python backtests/fvg_sweep_backtest.py
# → results/fvg_sweep_<date>.html  (interactive Plotly report)
```

## Knowledge base

`knowledge/ict/` is a semantic layer — one file per concept, machine-parseable YAML frontmatter, Detection Rules sections that are the spec for code implementations. Concept slugs are bound to detector code via the `@concept("<slug>")` decorator in `src/ict/registry.py`.

Currently implemented detectors: `swing-points`, `fair-value-gap`, `daily-bias`, `model-2022`.

See [knowledge/ict/README.md](knowledge/ict/README.md) for the full concept index.

## Models

| Model | File | Status |
|---|---|---|
| ICT 2022 (FVG sweep) | `src/ict/models/ict/model_2022.py` | backtested |
| Sniper Model | `src/ict/models/ict/sniper_model.py` | implemented |
| Silver Bullet | `knowledge/ict/models/silver-bullet.md` | spec only |
| Unicorn | `knowledge/ict/models/unicorn.md` | spec only |
| Three Indians / Wolfe Wave | `knowledge/ict/models/three-indians.md` | spec only |

## Concept Lineage

How concepts compose into models. Re-generate after adding new concepts:

```bash
python scripts/lineage.py                  # print full diagram
python scripts/lineage.py model-2022       # single model's graph
python scripts/lineage.py --update-readme  # regenerate the section below
```

<!-- lineage-start -->
```mermaid
flowchart LR
    subgraph Concepts
        draw_on_liquidity["draw-on-liquidity"]
        fair_value_gap["fair-value-gap"]
        killzones["killzones"]
        liquidity_sweep_stop_hunt["liquidity-sweep-stop-hunt"]
        market_structure_shift["market-structure-shift"]
        ohlc_candle_profiles["ohlc-candle-profiles"]
        premium_discount["premium-discount"]
        relative_equal_highs_lows["relative-equal-highs-lows"]
        sessions_and_ranges["sessions-and-ranges"]
        smt_divergence["smt-divergence"]
        swing_points["swing-points"]
        targets_and_exits["targets-and-exits"]
    end
    subgraph Intermediate
        daily_bias["daily-bias"]
    end
    subgraph Models
        model_2022["model-2022"]
        sniper_model["sniper-model"]
    end

    draw_on_liquidity --> daily_bias
    premium_discount --> daily_bias
    ohlc_candle_profiles --> daily_bias
    swing_points --> draw_on_liquidity
    swing_points --> market_structure_shift
    daily_bias --> model_2022
    fair_value_gap --> model_2022
    killzones --> model_2022
    market_structure_shift --> model_2022
    relative_equal_highs_lows --> model_2022
    sessions_and_ranges --> model_2022
    targets_and_exits --> model_2022
    swing_points --> relative_equal_highs_lows
    daily_bias --> sniper_model
    liquidity_sweep_stop_hunt --> sniper_model
    smt_divergence --> sniper_model
    market_structure_shift --> sniper_model
```
<!-- lineage-end -->

## Disclaimer

For educational and research purposes only. Trading involves substantial risk of loss.
