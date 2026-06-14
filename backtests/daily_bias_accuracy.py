#!/usr/bin/env python3
"""
Daily Bias Accuracy Test — NQ
==============================

Walk-forward test: for each trading day, compute daily bias using only data
available before that day's open, then check whether the day actually moved
in the bias direction.

"Correct" is defined two ways:
  close_vs_open   — did the day close above (bullish) or below (bearish) its own open?
  close_vs_prior  — did the day close above (bullish) or below (bearish) the prior close?

Usage:
  .venv/bin/python backtests/daily_bias_accuracy.py
  .venv/bin/python backtests/daily_bias_accuracy.py --weeks 52
  .venv/bin/python backtests/daily_bias_accuracy.py --lookback 5 --dealing 10
  .venv/bin/python backtests/daily_bias_accuracy.py --start 2022-01-01 --end 2024-12-31
"""

import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ict import DataLoader
from ict.models.intermediate.daily_bias import daily_bias_components

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weeks',    type=int,   default=None,         help='Weeks of data to load (default: all)')
    parser.add_argument('--start',    type=str,   default=None,         help='Start date YYYY-MM-DD')
    parser.add_argument('--end',      type=str,   default=None,         help='End date YYYY-MM-DD')
    parser.add_argument('--lookback', type=int,   default=5,            help='Daily order-flow lookback bars (default 5)')
    parser.add_argument('--dealing',  type=int,   default=20,           help='Dealing range days (default 20)')
    parser.add_argument('--swing',    type=int,   default=2,            help='Swing lookback for DOL (default 2)')
    parser.add_argument('--no-4h',    action='store_true',              help='Disable 4H confirmation signal')
    args = parser.parse_args()

    warmup = max(args.dealing, args.lookback) + 5  # days of prior data needed before first signal

    print(f"Loading NQ data (data_dir={DATA_DIR}) ...")
    loader_1m = DataLoader(timeframe='1T', weeks=args.weeks, data_dir=DATA_DIR)
    df_1m = loader_1m.read_NQ().dropna(subset=['close'])

    # Resample to daily and 4H from 1m so we control the candle boundaries
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

    # Determine the date range to evaluate
    all_dates = df_daily_all.index
    if args.start:
        all_dates = all_dates[all_dates >= pd.Timestamp(args.start, tz=all_dates.tz)]
    if args.end:
        all_dates = all_dates[all_dates <= pd.Timestamp(args.end, tz=all_dates.tz)]

    print(f"Parameters: lookback={args.lookback}, dealing={args.dealing}, swing={args.swing}, 4H={'off' if args.no_4h else 'on'}")
    print(f"Evaluating {len(all_dates)} days ...\n")

    rows = []
    for day_ts in all_dates:
        # All daily/4H bars strictly before this day's open
        daily_prior = df_daily_all[df_daily_all.index < day_ts]
        if len(daily_prior) < warmup:
            continue  # not enough history yet

        df_4h_prior = None if args.no_4h else df_4h_all[df_4h_all.index < day_ts]

        components = daily_bias_components(
            daily_prior,
            lookback=args.lookback,
            dealing_range_days=args.dealing,
            swing_lookback=args.swing,
            df_4h=df_4h_prior,
        )
        bias = components['bias']
        if bias == 'neutral':
            continue  # no signal — don't score it

        row = df_daily_all.loc[day_ts]
        actual_open  = float(row['open'])
        actual_close = float(row['close'])
        prior_close  = float(daily_prior['close'].iloc[-1])

        correct_vs_open  = (bias == 'bullish' and actual_close > actual_open) or \
                           (bias == 'bearish' and actual_close < actual_open)
        correct_vs_prior = (bias == 'bullish' and actual_close > prior_close) or \
                           (bias == 'bearish' and actual_close < prior_close)

        rows.append({
            'date':              day_ts.date(),
            'bias':              bias,
            'order_flow':        components['order_flow'],
            'draw':              components['draw'],
            'four_h_structure':  components['four_h_structure'],
            'prior_day_midpoint': components['prior_day_midpoint'],
            'open':              actual_open,
            'close':             actual_close,
            'prior_close':       prior_close,
            'correct_vs_open':   correct_vs_open,
            'correct_vs_prior':  correct_vs_prior,
        })

    if not rows:
        print("No signals generated — check parameters or date range.")
        return

    df = pd.DataFrame(rows)

    # ── Overall stats ────────────────────────────────────────────────────────
    total        = len(df)
    n_bull       = (df['bias'] == 'bullish').sum()
    n_bear       = (df['bias'] == 'bearish').sum()
    acc_open     = df['correct_vs_open'].mean()
    acc_prior    = df['correct_vs_prior'].mean()

    print("=" * 55)
    print("DAILY BIAS ACCURACY — NQ")
    print("=" * 55)
    print(f"  Signal days   : {total}  (bull={n_bull}, bear={n_bear})")
    print(f"  Accuracy vs open  : {acc_open:.1%}")
    print(f"  Accuracy vs prior close: {acc_prior:.1%}")

    # ── By direction ─────────────────────────────────────────────────────────
    print()
    for side in ('bullish', 'bearish'):
        sub = df[df['bias'] == side]
        if len(sub) == 0:
            continue
        print(f"  {side.upper()} ({len(sub)} days)")
        print(f"    vs open : {sub['correct_vs_open'].mean():.1%}")
        print(f"    vs prior: {sub['correct_vs_prior'].mean():.1%}")

    # ── By year ──────────────────────────────────────────────────────────────
    df['year'] = pd.to_datetime(df['date']).dt.year
    print()
    print("  By year (vs open):")
    for yr, grp in df.groupby('year'):
        print(f"    {yr}: {grp['correct_vs_open'].mean():.1%}  (n={len(grp)}, bull={( grp['bias']=='bullish').sum()}, bear={(grp['bias']=='bearish').sum()})")

    # ── Neutral rate ─────────────────────────────────────────────────────────
    all_day_count = len(all_dates) - warmup  # approximate (warmup days skipped)
    neutral_rate  = 1 - total / max(all_day_count, 1)
    print()
    print(f"  Days with no signal (neutral): ~{neutral_rate:.1%}")
    print("=" * 55)

    # ── Save ─────────────────────────────────────────────────────────────────
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results'))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'daily_bias_accuracy.csv')
    df.to_csv(out_path, index=False)
    print(f"\nDetailed results saved to: {out_path}")


if __name__ == '__main__':
    main()
