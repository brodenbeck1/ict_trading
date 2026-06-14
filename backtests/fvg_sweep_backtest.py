#!/usr/bin/env python3
"""
FVG Sweep Model Backtester — ICT 2022 Model on NQ
==================================================

Walk-forward backtest on NQ futures. Configurable via YAML (--config) or
run with defaults (no bias gate, wick stop, all pools).

Usage:
  python fvg_sweep_backtest.py                          # uses defaults
  python fvg_sweep_backtest.py --config configs/model_2022/baseline.yaml

Config keys (all optional — missing keys use model/backtest defaults):
  name            str    experiment name → results/<name>/ output dir
  description     str    human note, not used in code
  start_date      str    backtest start, e.g. '2024-11-01'
  instrument      str    'NQ' (only NQ supported today)
  use_daily_bias  bool   True = use bias gate; False = try both directions (default False)
  <model keys>    any    any key in Model2022.DEFAULT_CONFIG is forwarded to the model

Outputs (written to results/<name>/):
  *_trades.csv   — full trade log
  *_equity.png   — equity curve
  *_report.html  — interactive Plotly multi-timeframe report
"""

import argparse
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from plot_trades import (
    localize_to, eod_utc,
    simulate_fill, simulate_exit, calc_pnl_pts,
    compute_stats, print_stats, plot_equity_curve,
)

from ict import DataLoader, Model2022, Model2022Snapshot
from ict.backtest import Mark, TradeViz, build_report

# ─── Constants ───────────────────────────────────────────────────────────────

NQ_DOLLARS_PER_POINT = 20.0
DEFAULT_START_DATE   = '2024-11-01'
DEFAULT_INSTRUMENT   = 'NQ'
WARMUP_WEEKS         = 14
EOD_EXIT_HOUR        = 16

DATA_DIR     = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))
BASE_OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results/runs'))

# Keys consumed by the backtest runner; everything else goes to Model2022(config=...)
BACKTEST_KEYS = {'name', 'description', 'start_date', 'instrument', 'use_daily_bias'}


# ─── Snapshot builder ────────────────────────────────────────────────────────

def build_snapshot(df_1m: pd.DataFrame, session_ts: pd.Timestamp) -> Model2022Snapshot:
    d_naive = pd.Timestamp(session_ts.date())
    d = d_naive.tz_localize('UTC') if df_1m.index.tz is not None else d_naive

    df_2m = (
        df_1m.loc[d - pd.Timedelta(days=5): d + pd.Timedelta(days=1)]
        .resample('2min').agg({'open': 'first', 'high': 'max', 'low': 'min',
                               'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    df_15m = (
        df_1m.loc[d - pd.Timedelta(days=14): d + pd.Timedelta(days=1)]
        .resample('15min').agg({'open': 'first', 'high': 'max', 'low': 'min',
                                'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    df_daily = (
        df_1m.loc[d - pd.Timedelta(days=45): d - pd.Timedelta(minutes=1)]
        .resample('D').agg({'open': 'first', 'high': 'max', 'low': 'min',
                            'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    df_4h = (
        df_1m.loc[d - pd.Timedelta(days=45): d - pd.Timedelta(minutes=1)]
        .resample('4h').agg({'open': 'first', 'high': 'max', 'low': 'min',
                             'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    return Model2022Snapshot(
        df_2m=df_2m, df_15m=df_15m, df_daily=df_daily, session_date=session_ts,
        df_4h=df_4h,
    )


# ─── Plotly report adapter ───────────────────────────────────────────────────

C_ENTRY, C_STOP, C_TARGET = '#1f77b4', '#c0392b', '#1a8a4a'
C_FVG, C_SWEEP, C_MSS, C_BIAS = '#f39c12', '#8e44ad', '#16a085', '#7f8c8d'


def _window(df: pd.DataFrame, lo: pd.Timestamp, hi: pd.Timestamp) -> pd.DataFrame:
    lo = localize_to(lo, df.index)
    hi = localize_to(hi, df.index)
    return df.loc[lo:hi]


def trade_panels(snap: Model2022Snapshot, session_ts: pd.Timestamp) -> dict:
    d = pd.Timestamp(session_ts.date())
    session_day_bar = (
        snap.df_2m
        .resample('D').agg({'open': 'first', 'high': 'max', 'low': 'min',
                            'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    d_loc = localize_to(d, session_day_bar.index)
    session_day_bar = session_day_bar[session_day_bar.index.normalize() == d_loc]
    daily_display = pd.concat([snap.df_daily.tail(30), session_day_bar])
    daily_display = daily_display[~daily_display.index.duplicated(keep='last')]
    return {
        'daily': daily_display,
        '15m':   _window(snap.df_15m, d - pd.Timedelta(days=5), d + pd.Timedelta(days=1)),
        '2m':    _window(snap.df_2m,  d, d + pd.Timedelta(days=1)),
    }


def signal_to_marks(signal: dict, fill: dict, exit_info: dict) -> list:
    direction = signal['direction']
    marks = []
    g = 'Entry/Stop/Target'
    marks += [
        Mark('level',  g, '2m', f"Entry {signal['entry']:.2f}",   C_ENTRY,  price=signal['entry']),
        Mark('level',  g, '2m', f"Stop {signal['stop']:.2f}",     C_STOP,   dash='dash', price=signal['stop']),
        Mark('level',  g, '2m', f"Target {signal['target']:.2f}", C_TARGET, dash='dash', price=signal['target']),
        Mark('marker', g, '2m', "Fill", C_ENTRY,
             time=fill['fill_time'], price=fill['fill_price'], symbol='circle'),
    ]
    if exit_info:
        col = (C_TARGET if exit_info['exit_reason'] == 'target'
               else C_STOP if exit_info['exit_reason'] == 'stop' else C_BIAS)
        marks.append(Mark('marker', g, '2m', f"Exit ({exit_info['exit_reason']})", col,
                          time=exit_info['exit_time'], price=exit_info['exit_price'], symbol='x'))

    if signal.get('fvg_top') is not None:
        marks.append(Mark('zone', 'FVG', '2m', "FVG", C_FVG,
                          y0=signal['fvg_bottom'], y1=signal['fvg_top'],
                          t0=signal['entry_time'],
                          t1=(exit_info['exit_time'] if exit_info else None)))

    if signal.get('sweep_time') is not None:
        lbl = f"Sweep {signal.get('swept_pool') or ''}".strip()
        marks.append(Mark('marker', 'Sweep', '2m', lbl, C_SWEEP,
                          time=signal['sweep_time'], price=signal['sweep_level'],
                          symbol='x', default_on=True))
        marks.append(Mark('level', 'Sweep', '15m', f"Swept pool {signal['sweep_level']:.2f}",
                          C_SWEEP, dash='dot', price=signal['sweep_level'], default_on=True))
        cluster = signal.get('swept_cluster') or {}
        source  = cluster.get('source', '')
        price   = cluster.get('price', signal['sweep_level'])
        if source in ('OR-high', 'OR-low'):
            or_high = price if source == 'OR-high' else cluster.get('range_high', price)
            or_low  = price if source == 'OR-low'  else cluster.get('range_low',  price)
            t0, t1  = cluster.get('range_start'), cluster.get('range_end')
            if t0 is not None and t1 is not None:
                marks.append(Mark('zone', 'Sweep', '2m', 'Opening Range', C_SWEEP,
                                  y0=or_low, y1=or_high, t0=t0, t1=t1, default_on=True))
            for ts in cluster.get('timestamps', []):
                marks.append(Mark('marker', 'Sweep', '2m', f"Pool: {source} {price:.2f}",
                                  C_SWEEP, time=ts, price=price, symbol='diamond', default_on=True))
        elif source in ('PDH', 'PDL'):
            for ts in cluster.get('timestamps', []):
                marks.append(Mark('marker', 'Sweep', 'daily', f"Pool: {source} {price:.2f}",
                                  C_SWEEP, time=ts, price=price, symbol='diamond', default_on=True))
        else:
            for ts in cluster.get('timestamps', []):
                marks.append(Mark('marker', 'Sweep', '15m', f"Pool: {source} {price:.2f}",
                                  C_SWEEP, time=ts, price=price, symbol='diamond', default_on=True))

    if signal.get('bms_time') is not None:
        sym = 'triangle-down' if direction == 'short' else 'triangle-up'
        marks.append(Mark('marker', 'MSS', '2m', f"MSS {signal['bms_swing_level']:.2f}", C_MSS,
                          time=signal['bms_time'], price=signal['bms_swing_level'],
                          symbol=sym, default_on=True))
        marks.append(Mark('level', 'MSS', '2m', "MSS swing", C_MSS, dash='dot',
                          price=signal['bms_swing_level'], default_on=True))
    return marks


# ─── Main loop ───────────────────────────────────────────────────────────────

def run_backtest(
    run_config: dict = None,
    verbose: bool = True,
    save_outputs: bool = True,
    df_1m_cache: pd.DataFrame = None,
) -> dict:
    """
    Run the backtest and return a stats dict.

    Args:
        run_config:   Flat dict of config overrides (BACKTEST_KEYS + model keys).
                      None uses all defaults.
        verbose:      Print progress and stats to stdout.
        save_outputs: Write CSV, PNG, and HTML to results dir.
        df_1m_cache:  Pre-loaded 1m DataFrame to skip re-loading (for grid search).

    Returns:
        dict with 'name', 'config', 'n_trades', 'n_signals', and all compute_stats keys.
    """
    cfg = run_config or {}

    name           = cfg.get('name', 'baseline')
    start_date     = cfg.get('start_date', DEFAULT_START_DATE)
    instrument     = cfg.get('instrument', DEFAULT_INSTRUMENT).upper()
    use_daily_bias = cfg.get('use_daily_bias', False)

    model_config = {k: v for k, v in cfg.items() if k not in BACKTEST_KEYS}
    model        = Model2022(config=model_config)

    out_dir = os.path.join(BASE_OUT_DIR, name)
    if save_outputs:
        os.makedirs(out_dir, exist_ok=True)

    stem = f"fvg_sweep_{instrument.lower()}"

    # Directions to evaluate per day
    directions = (None,) if use_daily_bias else ('bearish', 'bullish')

    # ── Load data ────────────────────────────────────────────────────────────
    start_dt     = pd.Timestamp(start_date)
    warmup_start = start_dt - pd.Timedelta(weeks=WARMUP_WEEKS)
    weeks_needed = int((pd.Timestamp.now() - warmup_start).days / 7) + 4

    if df_1m_cache is not None:
        df_1m = df_1m_cache
    else:
        if verbose:
            print(f"Loading {instrument} 1m data (~{weeks_needed} weeks from {warmup_start.date()})...")
        loader = DataLoader(timeframe='1min', weeks=weeks_needed, data_dir=DATA_DIR)
        df_1m  = getattr(loader, f'read_{instrument}')()
        if verbose:
            print(f"  Loaded {len(df_1m):,} rows  {df_1m.index[0]} → {df_1m.index[-1]}")

    raw_idx_full = df_1m.index
    if raw_idx_full.tz is None:
        raw_idx_full = raw_idx_full.tz_localize('UTC')
    cutoff_utc = start_dt.tz_localize('UTC')
    df_bt = (df_1m[raw_idx_full >= cutoff_utc] if df_1m.index.tz is not None
             else df_1m[df_1m.index >= start_dt])

    raw_idx = df_bt.index
    if raw_idx.tz is None:
        raw_idx = raw_idx.tz_localize('UTC')
    ny_idx = raw_idx.tz_convert('America/New_York')
    session_mask_arr = ((ny_idx.hour * 60 + ny_idx.minute >= 8 * 60 + 30) &
                        (ny_idx.hour * 60 + ny_idx.minute <  11 * 60))
    trading_days = sorted(set(ny_idx.date[session_mask_arr]))
    if verbose:
        print(f"  {len(trading_days)} trading days  {trading_days[0]} → {trading_days[-1]}\n")

    # ── Walk-forward loop ─────────────────────────────────────────────────────
    trade_log  = []
    viz_trades = []
    n_signals  = 0
    n_no_fill  = 0
    n_errors   = 0

    for i, day in enumerate(trading_days):
        session_ts = pd.Timestamp(day)
        try:
            snap = build_snapshot(df_1m, session_ts)
        except Exception as exc:
            n_errors += 1
            if verbose:
                print(f"  ERROR {day}: {exc}")
            continue

        for forced_dir in directions:
            try:
                signal = model.generate_signal(snap, force_direction=forced_dir)
            except Exception as exc:
                n_errors += 1
                if verbose:
                    print(f"  ERROR {day} {forced_dir}: {exc}")
                continue

            if not signal['actionable']:
                continue
            n_signals += 1

            fill = simulate_fill(snap.df_2m, signal, session_ts, EOD_EXIT_HOUR)
            if fill is None:
                n_no_fill += 1
                continue

            exit_info = simulate_exit(snap.df_2m, signal, fill, session_ts, EOD_EXIT_HOUR)
            pnl_pts   = calc_pnl_pts(signal['direction'], fill['fill_price'], exit_info['exit_price'])
            pnl_usd   = round(pnl_pts * NQ_DOLLARS_PER_POINT, 2)

            trade_log.append({
                'session_date': str(day),
                'direction':    signal['direction'],
                'entry_price':  round(fill['fill_price'], 2),
                'entry_time':   str(fill['fill_time']),
                'stop':         round(signal['stop'], 2),
                'target':       round(signal['target'], 2),
                'exit_price':   round(exit_info['exit_price'], 2),
                'exit_time':    str(exit_info['exit_time']),
                'exit_reason':  exit_info['exit_reason'],
                'risk_pts':     round(abs(signal['stop'] - signal['entry']), 2),
                'reward_pts':   round(abs(signal['target'] - signal['entry']), 2),
                'pnl_pts':      round(pnl_pts, 2),
                'pnl_usd':      pnl_usd,
            })

            if save_outputs:
                viz_trades.append(TradeViz(
                    label=f"{day}  {signal['direction'].upper()}  ${pnl_usd:,.0f}",
                    panels=trade_panels(snap, session_ts),
                    marks=signal_to_marks(signal, fill, exit_info),
                    pnl=pnl_usd,
                ))

        if verbose and (i + 1) % 50 == 0:
            pnl_so_far = sum(t['pnl_usd'] for t in trade_log)
            print(f"  Day {i+1:>3}/{len(trading_days)}  "
                  f"signals={n_signals}  trades={len(trade_log)}  "
                  f"P&L=${pnl_so_far:,.0f}")

    if verbose:
        print(f"\n── Summary ──────────────────────────────────────────")
        print(f"  Days evaluated : {len(trading_days)}")
        print(f"  Signals fired  : {n_signals}")
        print(f"  No-fill        : {n_no_fill}")
        print(f"  Filled trades  : {len(trade_log)}")
        print(f"  Errors         : {n_errors}")

    if not trade_log:
        if verbose:
            print("\nNo trades executed.")
        return {'name': name, 'config': cfg, 'n_trades': 0, 'n_signals': n_signals}

    trades = pd.DataFrame(trade_log)
    stats  = compute_stats(trades)

    if verbose:
        print()
        print_stats(stats, f'{name}  ({instrument}, {start_date}→)')
        trades['month'] = pd.to_datetime(trades['session_date']).dt.to_period('M')
        print(f"\n  {'Month':<10} {'Trades':>6}  {'Wins':>4}  {'P&L pts':>9}  {'P&L $':>9}")
        print(f"  {'-'*45}")
        for month, grp in trades.groupby('month'):
            w = (grp['exit_reason'] == 'target').sum()
            print(f"  {str(month):<10} {len(grp):>6}  {w:>4}  "
                  f"{grp['pnl_pts'].sum():>9.1f}  {grp['pnl_usd'].sum():>9,.0f}")

    if save_outputs:
        log_path = os.path.join(out_dir, f'{stem}_trades.csv')
        trades.to_csv(log_path, index=False)
        if verbose:
            print(f"\nTrade log → {log_path}")

        chart_path = os.path.join(out_dir, f'{stem}_equity.png')
        plot_equity_curve(
            trades, chart_path,
            title=f'{name} — {instrument}  {start_date}→  (1 contract, ${NQ_DOLLARS_PER_POINT}/pt)',
        )
        if verbose:
            print(f"Equity curve → {chart_path}")

        report_stats = {
            'Trades':          stats['total_trades'],
            'Win rate':        f"{stats['win_rate']}%  ({stats['wins']}W / {stats['losses']}L / {stats['eods']} EOD)",
            'Total P&L':       f"${stats['total_pnl_usd']:,.2f}  ({stats['total_pnl_pts']:.1f} pts)",
            'Avg R:R (setup)': stats['avg_rr'],
            'Profit factor':   stats['profit_factor'],
            'Max drawdown':    f"${stats['max_dd_usd']:,.2f}",
            'Sharpe':          stats['sharpe_ratio'],
        }
        report_path = os.path.join(out_dir, f'{stem}_report.html')
        build_report(
            trades=viz_trades,
            panel_order=['daily', '15m', '2m'],
            out_path=report_path,
            title=f'{name} — {instrument}  {start_date}→',
            equity=trades['pnl_usd'].cumsum(),
            stats=report_stats,
        )
        if verbose:
            print(f"Interactive report → {report_path}")

    return {'name': name, 'config': cfg, 'n_trades': len(trade_log),
            'n_signals': n_signals, **stats}


# ─── CLI entry point ─────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FVG Sweep backtest — ICT 2022 Model')
    parser.add_argument('--config', default=None,
                        help='Path to a YAML experiment config file')
    args = parser.parse_args()

    run_cfg = {}
    if args.config:
        import yaml
        with open(args.config) as f:
            run_cfg = yaml.safe_load(f) or {}
        print(f"Config: {args.config}  ({run_cfg.get('name', '?')})")

    run_backtest(run_cfg)
