#!/usr/bin/env python3
"""
grid_search.py — Automated cross-product parameter search for Model2022.

Defines a BASE_CONFIG and a PARAM_GRID. Every combination of grid values is
run through run_backtest() (no file outputs, no printing) and the results are
ranked and saved.

Usage:
  python grid_search.py                     # uses the grid defined below
  python grid_search.py --out my_grid.csv   # custom output path
  python grid_search.py --sort sharpe       # sort column

Edit PARAM_GRID below to control what gets swept.

Output:
  results/grid_search_<timestamp>.csv  — all combinations ranked by profit_factor
"""

import argparse
import itertools
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from fvg_sweep_backtest import run_backtest, DATA_DIR, DEFAULT_START_DATE, WARMUP_WEEKS
from ict import DataLoader

BASE_RESULTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results/grids'))

# ─── Experiment definition ───────────────────────────────────────────────────
#
# BASE_CONFIG: defaults applied to every run (these won't be varied).
# PARAM_GRID:  dict of param → list of values to try.
#              All combinations are crossed via itertools.product.
#
# To add a new axis: just add a key to PARAM_GRID with a list of values.
# To fix a parameter: put it in BASE_CONFIG (or remove it from PARAM_GRID).

BASE_CONFIG = {
    'start_date':    DEFAULT_START_DATE,
    'instrument':    'NQ',
    'target_min_rr': 3.0,
    'killzones': [('02:00', '05:00'), ('07:00', '10:00'), ('13:30', '16:00')],
    'stop_mode':     'wick',
    'max_stop_pts':  20.0,
}

PARAM_GRID = {
    'use_daily_bias':       [False, True],
    'use_pdh_pdl':          [True, False],
    'use_ons':              [True, False],
    'use_opening_range':    [True, False],
    'use_reh_rel':          [True, False],
}

CONDITIONAL_PARAMS = {}

SORT_ALIASES = {
    'pf':     'profit_factor',
    'sharpe': 'sharpe_ratio',
    'pnl':    'total_pnl_pts',
}


def build_combinations(grid: dict, conditionals: dict) -> list[dict]:
    keys   = list(grid.keys())
    combos = list(itertools.product(*[grid[k] for k in keys]))
    result = []
    for combo in combos:
        cfg = dict(zip(keys, combo))

        # Expand conditional params
        conditional_axes = {}
        for child_key, spec in conditionals.items():
            parent_key, req_val = spec['when']
            if cfg.get(parent_key) == req_val:
                conditional_axes[child_key] = spec['values']

        if conditional_axes:
            cond_keys   = list(conditional_axes.keys())
            cond_combos = list(itertools.product(*[conditional_axes[k] for k in cond_keys]))
            for cond_combo in cond_combos:
                full = {**cfg, **dict(zip(cond_keys, cond_combo))}
                result.append(full)
        else:
            result.append(cfg)

    return result


def combo_name(cfg: dict, base: dict) -> str:
    """Short name from the varied keys."""
    parts = []
    for k, v in sorted(cfg.items()):
        if k in ('start_date', 'instrument', 'killzones'):
            continue
        if isinstance(v, bool):
            parts.append(f"{k[4:] if k.startswith('use_') else k}={'Y' if v else 'N'}")
        elif isinstance(v, float) and v == int(v):
            parts.append(f"{k}={int(v)}")
        else:
            parts.append(f"{k}={v}")
    return '|'.join(parts) or 'default'


def main():
    parser = argparse.ArgumentParser(description='Grid search over Model2022 params')
    parser.add_argument('--out', default=None, help='Output CSV path')
    parser.add_argument('--sort', default='profit_factor', help='Column to sort by')
    args = parser.parse_args()

    sort_key = SORT_ALIASES.get(args.sort, args.sort)

    combos = build_combinations(PARAM_GRID, CONDITIONAL_PARAMS)
    total  = len(combos)
    print(f"Grid search: {total} combinations\n")

    # Load data once and reuse across all runs
    start_dt     = pd.Timestamp(DEFAULT_START_DATE)
    warmup_start = start_dt - pd.Timedelta(weeks=WARMUP_WEEKS)
    weeks_needed = int((pd.Timestamp.now() - warmup_start).days / 7) + 4
    print(f"Loading NQ 1m data (~{weeks_needed} weeks)...")
    loader = DataLoader(timeframe='1min', weeks=weeks_needed, data_dir=DATA_DIR)
    df_1m  = loader.read_NQ()
    print(f"  Loaded {len(df_1m):,} rows\n")

    rows   = []
    t0     = time.time()

    for i, combo in enumerate(combos):
        run_cfg = {**BASE_CONFIG, **combo}
        run_cfg['name'] = combo_name(combo, BASE_CONFIG)

        try:
            stats = run_backtest(
                run_config=run_cfg,
                verbose=False,
                save_outputs=False,
                df_1m_cache=df_1m,
            )
        except Exception as exc:
            print(f"  [{i+1}/{total}] ERROR {run_cfg['name']}: {exc}")
            continue

        row = {**combo, **{k: v for k, v in stats.items()
                           if k not in ('name', 'config')}}
        rows.append(row)

        elapsed = time.time() - t0
        eta     = elapsed / (i + 1) * (total - i - 1)
        pf      = stats.get('profit_factor', 0)
        trades  = stats.get('n_trades', 0)
        print(f"  [{i+1:>4}/{total}]  {run_cfg['name'][:60]:<60}  "
              f"trades={trades:>3}  PF={pf:.2f}  ETA {eta/60:.1f}m")

    if not rows:
        print("No results.")
        return

    df = pd.DataFrame(rows)
    if sort_key in df.columns:
        ascending = sort_key in ('max_dd_usd',)
        df = df.sort_values(sort_key, ascending=ascending)

    ts      = time.strftime('%Y%m%d_%H%M%S')
    out_path = args.out or os.path.join(BASE_RESULTS, f'grid_search_{ts}.csv')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"\nSaved {len(df)} results → {out_path}")

    # Print top 10
    display_cols = ['profit_factor', 'sharpe_ratio', 'total_pnl_pts', 'win_rate',
                    'n_trades', 'max_dd_usd']
    print(f"\nTop 10 by {sort_key}:")
    print(f"  {'Combo':<65}  {'PF':>5}  {'Sharpe':>7}  {'P&L pts':>9}  {'WR%':>5}  {'Trades':>6}  {'MaxDD':>9}")
    print("─" * 120)
    for _, row in df.head(10).iterrows():
        name = combo_name({k: row[k] for k in PARAM_GRID if k in row}, BASE_CONFIG)
        print(
            f"  {name[:63]:<65}  "
            f"{row.get('profit_factor', 0):>5.2f}  "
            f"{row.get('sharpe_ratio', 0):>7.2f}  "
            f"{row.get('total_pnl_pts', 0):>9.1f}  "
            f"{row.get('win_rate', 0):>5.1f}  "
            f"{int(row.get('n_trades', 0)):>6}  "
            f"${row.get('max_dd_usd', 0):>8,.0f}"
        )


if __name__ == '__main__':
    main()
