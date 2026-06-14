# Experiment Configs & Infrastructure

Named YAML configs and the tooling that runs them. Three-layer system for parameterizing and comparing model configurations.

> Referenced from `CLAUDE.md`. Read this when running a single config, comparing runs, or doing a grid search.

---

## 1. Model config flags (Option C)

All knobs live in `Model2022.DEFAULT_CONFIG`. Pass a dict to `Model2022(config={...})` to override any key.

**Pool toggles** (all `bool`, default `True`):
`use_pdh_pdl`, `use_ons`, `use_chicago_prior`, `use_chicago_same_day`, `use_opening_range`, `use_reh_rel`

**Stop modes** (`stop_mode` key):
| Value | Description |
|---|---|
| `'wick'` | Stop at swept wick extreme, capped by `max_stop_pts` |
| `'atr'` | Stop at `entry ± stop_atr_mult × ATR(stop_atr_period)` on 2m bars, capped by `max_stop_pts` |
| `'fixed'` | Stop at `entry ± stop_fixed_pts`, capped by `max_stop_pts` |

**Other model keys**: `max_stop_pts`, `target_min_rr`, `killzones`, `max_bars_sweep_to_mss`, `eq_tolerance_pts`, `reh_lookback_days`, `swing_lookback`, `daily_lookback`, `dealing_range_days`

---

## 2. Named YAML configs + single-run backtest (Option A)

```
configs/model_2022/          # one file per named experiment
  baseline.yaml              # current production config
  with_bias.yaml
  pdh_pdl_only.yaml
  london_only.yaml
```

**YAML schema** (all keys optional — missing keys use defaults):
```yaml
name: my_experiment          # → results/my_experiment/ output dir
description: "human note"
start_date: "2024-11-01"
instrument: NQ
use_daily_bias: false        # false = try both directions per day
# any Model2022.DEFAULT_CONFIG key can go here:
stop_mode: wick
max_stop_pts: 20.0
use_pdh_pdl: true
killzones:
  - ["02:00", "05:00"]
  - ["07:00", "10:00"]
```

**Run a single config:**
```bash
.venv/bin/python backtests/fvg_sweep_backtest.py --config configs/model_2022/baseline.yaml
```

**Compare all runs:**
```bash
.venv/bin/python backtests/compare_runs.py                     # all results/ dirs
.venv/bin/python backtests/compare_runs.py baseline with_bias  # named only
.venv/bin/python backtests/compare_runs.py --sort sharpe --save
```

---

## 3. Automated grid search (Option B)

Edit `PARAM_GRID` in `backtests/grid_search.py` to define which parameters to sweep and what values to try. Uses `itertools.product` for the full cross-product. Data is loaded once and reused.

```bash
.venv/bin/python backtests/grid_search.py
.venv/bin/python backtests/grid_search.py --sort sharpe --out results/my_grid.csv
```

**Warning**: grid explodes fast. 2 bias × 3 stop modes × 4 max_stop × 2 PDH × 2 ONS × 2 OR × 2 REH = 192 runs. Use `BASE_CONFIG` to fix parameters that are already decided, and keep `PARAM_GRID` to the axes you're actively investigating.
