#!/usr/bin/env python3
"""
compare_runs.py — Compare backtest results across experiment configs.

Scans results/<name>/*_trades.csv, computes stats for each, and prints
a ranked table sorted by profit factor (descending).

Usage:
  python compare_runs.py                    # scans all results/ subdirs
  python compare_runs.py baseline with_bias # compare named runs only
  python compare_runs.py --sort sharpe      # sort by a different column
  python compare_runs.py --save             # write results/comparison.csv
"""

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from plot_trades import compute_stats

BASE_RESULTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results/runs'))

SORT_ALIASES = {
    'pf':     'profit_factor',
    'sharpe': 'sharpe_ratio',
    'pnl':    'total_pnl_pts',
    'dd':     'max_dd_usd',
    'wr':     'win_rate',
}


def load_run(name: str) -> dict | None:
    run_dir = os.path.join(BASE_RESULTS, name)
    csvs = [f for f in os.listdir(run_dir) if f.endswith('_trades.csv')]
    if not csvs:
        return None
    trades = pd.read_csv(os.path.join(run_dir, csvs[0]))
    if trades.empty:
        return None
    stats = compute_stats(trades)
    return {'name': name, **stats}


def main():
    parser = argparse.ArgumentParser(description='Compare backtest runs')
    parser.add_argument('runs', nargs='*', help='Run names to compare (default: all)')
    parser.add_argument('--sort', default='profit_factor',
                        help='Column to sort by (pf, sharpe, pnl, dd, wr, or full key)')
    parser.add_argument('--save', action='store_true', help='Save comparison.csv')
    args = parser.parse_args()

    sort_key = SORT_ALIASES.get(args.sort, args.sort)

    if args.runs:
        names = args.runs
    else:
        try:
            names = [d for d in os.listdir(BASE_RESULTS)
                     if os.path.isdir(os.path.join(BASE_RESULTS, d))]
        except FileNotFoundError:
            print(f"Results directory not found: {BASE_RESULTS}")
            return

    rows = []
    for name in sorted(names):
        try:
            row = load_run(name)
            if row:
                rows.append(row)
            else:
                print(f"  skip {name}: no trades CSV or empty")
        except Exception as e:
            print(f"  skip {name}: {e}")

    if not rows:
        print("No runs found.")
        return

    df = pd.DataFrame(rows)

    if sort_key in df.columns:
        ascending = sort_key in ('max_dd_usd',)
        df = df.sort_values(sort_key, ascending=ascending)
    else:
        print(f"  Warning: sort key '{sort_key}' not found, showing unsorted")

    cols = ['name', 'total_trades', 'win_rate', 'profit_factor', 'sharpe_ratio',
            'total_pnl_pts', 'total_pnl_usd', 'max_dd_usd', 'avg_win_pts', 'avg_loss_pts']
    display = df[[c for c in cols if c in df.columns]]

    # pretty print
    print(f"\n{'Name':<25}  {'Trades':>6}  {'WR%':>5}  {'PF':>5}  {'Sharpe':>7}  "
          f"{'P&L pts':>9}  {'P&L $':>10}  {'MaxDD':>9}  {'AvgW':>6}  {'AvgL':>6}")
    print("─" * 105)
    for _, row in display.iterrows():
        print(
            f"  {str(row['name']):<23}  "
            f"{int(row.get('total_trades', 0)):>6}  "
            f"{row.get('win_rate', 0):>5.1f}  "
            f"{row.get('profit_factor', 0):>5.2f}  "
            f"{row.get('sharpe_ratio', 0):>7.2f}  "
            f"{row.get('total_pnl_pts', 0):>9.1f}  "
            f"${row.get('total_pnl_usd', 0):>9,.0f}  "
            f"${row.get('max_dd_usd', 0):>8,.0f}  "
            f"{row.get('avg_win_pts', 0):>6.1f}  "
            f"{row.get('avg_loss_pts', 0):>6.1f}"
        )
    print()

    if args.save:
        out_path = os.path.join(BASE_RESULTS, '..', 'comparison.csv')
        out_path = os.path.normpath(out_path)
        df.to_csv(out_path, index=False)
        print(f"Saved → {out_path}")


if __name__ == '__main__':
    main()
