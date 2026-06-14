#!/usr/bin/env python3
"""
Daily Bias Grid Search
=======================

Tests every combination of:
  - Parameter sets  (lookback, dealing_range_days, swing_lookback)
  - Gate combos     (which sub-signals must agree to produce a non-neutral bias)

For each combination reports: signal frequency, neutral rate, bull/bear accuracy,
overall accuracy, and a coverage score (accuracy × signal_rate) that balances
being right with having enough signals to trade.

Two-pass design for speed:
  1. Compute component dicts for all days under each param set (expensive, done once).
  2. Apply all gate combos to those stored components (cheap).

Usage:
  .venv/bin/python backtests/daily_bias_grid_search.py
  .venv/bin/python backtests/daily_bias_grid_search.py --sort coverage_score
  .venv/bin/python backtests/daily_bias_grid_search.py --out results/my_bias_grid.csv
  .venv/bin/python backtests/daily_bias_grid_search.py --start 2018-01-01
"""

import argparse
import itertools
import os
import sys
import time
from typing import Optional

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ict import DataLoader
from ict.models.intermediate.daily_bias import daily_bias_components

DATA_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results'))

# ─── Parameter grid ──────────────────────────────────────────────────────────

PARAM_GRID = {
    'lookback':           [3, 5, 10, 20, 30],
    'dealing_range_days': [10, 20, 40, 60],
    'swing_lookback':     [2, 3, 5],
}

# ─── Gate combos ─────────────────────────────────────────────────────────────
#
# Each gate is a function(row_dict) -> 'bullish' | 'bearish' | 'neutral'
# where row_dict has keys: order_flow, draw, four_h_structure, prior_day_midpoint
#
# 4H "soft":  neutral 4H abstains (does not veto an otherwise valid signal)
# 4H "hard":  neutral 4H vetoes   (4H must actively agree)
# PDM:        prior_day_midpoint treated as a strict gate signal


def _agree(signals: list, direction: str) -> bool:
    return all(s == direction for s in signals)


def gate_order_flow_only(r):
    return r['order_flow']


def gate_draw_only(r):
    return r['draw']


def gate_four_h_only(r):
    fh = r['four_h_structure']
    return fh if fh in ('bullish', 'bearish') else 'neutral'


def gate_of_draw(r):
    of, draw = r['order_flow'], r['draw']
    if of == draw == 'bullish':  return 'bullish'
    if of == draw == 'bearish':  return 'bearish'
    return 'neutral'


def gate_of_draw_4h_soft(r):
    """Current implementation: 4H neutral abstains."""
    of, draw, fh = r['order_flow'], r['draw'], r['four_h_structure']
    if of == draw == 'bullish' and fh in ('bullish', 'neutral'):  return 'bullish'
    if of == draw == 'bearish' and fh in ('bearish', 'neutral'):  return 'bearish'
    return 'neutral'


def gate_of_draw_4h_hard(r):
    """Strict: 4H must actively agree (neutral vetoes)."""
    of, draw, fh = r['order_flow'], r['draw'], r['four_h_structure']
    if of == draw == fh == 'bullish':  return 'bullish'
    if of == draw == fh == 'bearish':  return 'bearish'
    return 'neutral'


def gate_of_pdm(r):
    of, pdm = r['order_flow'], r['prior_day_midpoint']
    if of == pdm == 'bullish':  return 'bullish'
    if of == pdm == 'bearish':  return 'bearish'
    return 'neutral'


def gate_draw_pdm(r):
    draw, pdm = r['draw'], r['prior_day_midpoint']
    if draw == pdm == 'bullish':  return 'bullish'
    if draw == pdm == 'bearish':  return 'bearish'
    return 'neutral'


def gate_of_draw_pdm(r):
    of, draw, pdm = r['order_flow'], r['draw'], r['prior_day_midpoint']
    if of == draw == pdm == 'bullish':  return 'bullish'
    if of == draw == pdm == 'bearish':  return 'bearish'
    return 'neutral'


def gate_of_draw_4h_soft_pdm(r):
    of, draw, fh, pdm = (r['order_flow'], r['draw'],
                         r['four_h_structure'], r['prior_day_midpoint'])
    if of == draw == pdm == 'bullish' and fh in ('bullish', 'neutral'):  return 'bullish'
    if of == draw == pdm == 'bearish' and fh in ('bearish', 'neutral'):  return 'bearish'
    return 'neutral'


def gate_of_4h_soft(r):
    of, fh = r['order_flow'], r['four_h_structure']
    if of == 'bullish' and fh in ('bullish', 'neutral'):  return 'bullish'
    if of == 'bearish' and fh in ('bearish', 'neutral'):  return 'bearish'
    return 'neutral'


def gate_draw_4h_soft(r):
    draw, fh = r['draw'], r['four_h_structure']
    if draw == 'bullish' and fh in ('bullish', 'neutral'):  return 'bullish'
    if draw == 'bearish' and fh in ('bearish', 'neutral'):  return 'bearish'
    return 'neutral'


GATE_COMBOS = {
    'order_flow_only':     gate_order_flow_only,
    'draw_only':           gate_draw_only,
    'four_h_only':         gate_four_h_only,
    'of_draw':             gate_of_draw,
    'of_draw_4h_soft':     gate_of_draw_4h_soft,    # ← current implementation
    'of_draw_4h_hard':     gate_of_draw_4h_hard,
    'of_pdm':              gate_of_pdm,
    'draw_pdm':            gate_draw_pdm,
    'of_draw_pdm':         gate_of_draw_pdm,
    'of_4h_soft':          gate_of_4h_soft,
    'draw_4h_soft':        gate_draw_4h_soft,
    'of_draw_4h_soft_pdm': gate_of_draw_4h_soft_pdm,
}

# ─── Scoring ─────────────────────────────────────────────────────────────────


def score_rows(component_rows: list, gate_fn, total_days: int) -> Optional[dict]:
    """
    Apply a gate function to pre-computed component rows and return accuracy metrics.

    component_rows: list of dicts with keys order_flow, draw, four_h_structure,
                    prior_day_midpoint, actual_open, actual_close
    """
    n_bull_correct = n_bull_wrong = 0
    n_bear_correct = n_bear_wrong = 0

    for r in component_rows:
        bias = gate_fn(r)
        if bias == 'neutral':
            continue
        close, open_ = r['actual_close'], r['actual_open']
        if bias == 'bullish':
            if close > open_:  n_bull_correct += 1
            else:              n_bull_wrong   += 1
        else:
            if close < open_:  n_bear_correct += 1
            else:              n_bear_wrong   += 1

    n_bull   = n_bull_correct + n_bull_wrong
    n_bear   = n_bear_correct + n_bear_wrong
    n_signal = n_bull + n_bear

    if n_signal == 0:
        return None

    bull_acc    = n_bull_correct / n_bull   if n_bull   else float('nan')
    bear_acc    = n_bear_correct / n_bear   if n_bear   else float('nan')
    overall_acc = (n_bull_correct + n_bear_correct) / n_signal
    signal_rate = n_signal / max(total_days, 1)

    return {
        'n_signal':      n_signal,
        'n_bull':        n_bull,
        'n_bear':        n_bear,
        'neutral_rate':  round(1 - signal_rate, 4),
        'bull_acc':      round(bull_acc,    4),
        'bear_acc':      round(bear_acc,    4),
        'overall_acc':   round(overall_acc, 4),
        'coverage_score': round(overall_acc * signal_rate, 4),
    }


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sort',  default='coverage_score', help='Column to sort by')
    parser.add_argument('--out',   default=None,             help='Output CSV path')
    parser.add_argument('--start', default=None,             help='Start date YYYY-MM-DD')
    parser.add_argument('--end',   default=None,             help='End date YYYY-MM-DD')
    parser.add_argument('--top',   type=int, default=20,     help='Rows to print')
    args = parser.parse_args()

    print(f"Loading NQ 1m data (data_dir={DATA_DIR}) ...")
    t0 = time.time()
    loader = DataLoader(timeframe='1T', data_dir=DATA_DIR)
    df_1m  = loader.read_NQ().dropna(subset=['close'])
    print(f"  {len(df_1m):,} rows loaded in {time.time()-t0:.1f}s\n")

    df_daily_all = (
        df_1m.resample('D')
        .agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    df_4h_all = (
        df_1m.resample('4h')
        .agg({'open': 'first', 'high': 'max', 'low': 'min', 'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )

    all_dates = df_daily_all.index
    if args.start:
        all_dates = all_dates[all_dates >= pd.Timestamp(args.start, tz=all_dates.tz)]
    if args.end:
        all_dates = all_dates[all_dates <= pd.Timestamp(args.end, tz=all_dates.tz)]

    param_combos = list(itertools.product(
        *[PARAM_GRID[k] for k in ('lookback', 'dealing_range_days', 'swing_lookback')]
    ))
    n_params = len(param_combos)
    n_gates  = len(GATE_COMBOS)
    print(f"Parameter combos : {n_params}")
    print(f"Gate combos      : {n_gates}")
    print(f"Total result rows: {n_params * n_gates}")
    print(f"Evaluation days  : {len(all_dates)}\n")

    all_results = []
    t_start = time.time()

    for pi, (lookback, dealing, swing) in enumerate(param_combos):
        warmup = max(dealing, lookback) + 5

        # ── Pass 1: compute all components for this param set ─────────────────
        component_rows = []
        for day_ts in all_dates:
            daily_prior = df_daily_all[df_daily_all.index < day_ts]
            if len(daily_prior) < warmup:
                continue

            df_4h_prior = df_4h_all[df_4h_all.index < day_ts]

            try:
                comp = daily_bias_components(
                    daily_prior,
                    lookback=lookback,
                    dealing_range_days=dealing,
                    swing_lookback=swing,
                    df_4h=df_4h_prior,
                )
            except Exception:
                continue

            row = df_daily_all.loc[day_ts]
            component_rows.append({
                'order_flow':         comp['order_flow'],
                'draw':               comp['draw'],
                'four_h_structure':   comp['four_h_structure'],
                'prior_day_midpoint': comp['prior_day_midpoint'],
                'actual_open':        float(row['open']),
                'actual_close':       float(row['close']),
            })

        total_days = len(component_rows)

        # ── Pass 2: score each gate combo ─────────────────────────────────────
        for gate_name, gate_fn in GATE_COMBOS.items():
            metrics = score_rows(component_rows, gate_fn, total_days)
            if metrics is None:
                continue
            all_results.append({
                'gate':               gate_name,
                'lookback':           lookback,
                'dealing_range_days': dealing,
                'swing_lookback':     swing,
                **metrics,
            })

        elapsed = time.time() - t_start
        eta     = elapsed / (pi + 1) * (n_params - pi - 1)
        print(f"  [{pi+1:>3}/{n_params}]  lb={lookback:<3} deal={dealing:<3} sw={swing}  "
              f"{total_days} days  ETA {eta:.0f}s")

    if not all_results:
        print("No results generated.")
        return

    df = pd.DataFrame(all_results)

    sort_col = args.sort if args.sort in df.columns else 'coverage_score'
    df = df.sort_values(sort_col, ascending=False).reset_index(drop=True)

    # ── Save ─────────────────────────────────────────────────────────────────
    os.makedirs(RESULTS_DIR, exist_ok=True)
    ts       = time.strftime('%Y%m%d_%H%M%S')
    out_path = args.out or os.path.join(RESULTS_DIR, f'daily_bias_grid_{ts}.csv')
    df.to_csv(out_path, index=False)

    # ── Print top N ──────────────────────────────────────────────────────────
    top = args.top
    print(f"\nTop {top} by {sort_col}:")
    print(f"  {'gate':<22} {'lb':>4} {'deal':>5} {'sw':>3} "
          f"{'signals':>8} {'neutral%':>9} {'bull%':>7} {'bear%':>7} "
          f"{'acc%':>6} {'coverage':>9}")
    print("─" * 95)
    for _, row in df.head(top).iterrows():
        print(
            f"  {row['gate']:<22} {int(row['lookback']):>4} {int(row['dealing_range_days']):>5} "
            f"{int(row['swing_lookback']):>3} "
            f"{int(row['n_signal']):>8} {row['neutral_rate']:>9.1%} "
            f"{row['bull_acc']:>7.1%} {row['bear_acc']:>7.1%} "
            f"{row['overall_acc']:>6.1%} {row['coverage_score']:>9.4f}"
        )

    print(f"\nAll {len(df)} results saved → {out_path}")

    # ── Summary by gate (best param set per gate) ────────────────────────────
    print("\nBest param set per gate (by coverage_score):")
    print(f"  {'gate':<22} {'lb':>4} {'deal':>5} {'sw':>3} "
          f"{'signals':>8} {'neutral%':>9} {'bull%':>7} {'bear%':>7} "
          f"{'acc%':>6} {'coverage':>9}")
    print("─" * 95)
    best_per_gate = df.groupby('gate').first().reset_index()  # already sorted desc
    for _, row in best_per_gate.sort_values('coverage_score', ascending=False).iterrows():
        print(
            f"  {row['gate']:<22} {int(row['lookback']):>4} {int(row['dealing_range_days']):>5} "
            f"{int(row['swing_lookback']):>3} "
            f"{int(row['n_signal']):>8} {row['neutral_rate']:>9.1%} "
            f"{row['bull_acc']:>7.1%} {row['bear_acc']:>7.1%} "
            f"{row['overall_acc']:>6.1%} {row['coverage_score']:>9.4f}"
        )


if __name__ == '__main__':
    main()
