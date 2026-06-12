#!/usr/bin/env python3
"""
FVG Sweep Model Backtester — ICT 2022 Model on NQ
==================================================

Walk-forward backtest on NQ futures. Sweeps are taken in the London (02:00–05:00 NY)
and NY AM (07:00–10:00 NY) killzones; one signal evaluated per trading day.
Fixed 1 NQ contract ($20/pt).

Outputs:
  fvg_sweep_nq_trades.csv   — full trade log
  fvg_sweep_nq_equity.png   — equity curve + trade bar chart
  fvg_sweep_nq_report.html  — interactive multi-timeframe Plotly report
"""

import os
import sys
import pandas as pd

# shared backtest utilities live in plot_trades (same directory)
sys.path.insert(0, os.path.dirname(__file__))
from plot_trades import (
    localize_to, eod_utc,
    simulate_fill, simulate_exit, calc_pnl_pts,
    compute_stats, print_stats, plot_equity_curve,
)

from ict import DataLoader, Model2022, Model2022Snapshot
from ict.backtest import Mark, TradeViz, build_report

# ─── Config ──────────────────────────────────────────────────────────────────

NQ_DOLLARS_PER_POINT = 20.0
START_DATE   = '2024-11-01'
WARMUP_WEEKS = 14
EOD_EXIT_HOUR = 16

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))
OUT_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results/fvg_sweep_nq'))
os.makedirs(OUT_DIR, exist_ok=True)


# ─── Snapshot builder ────────────────────────────────────────────────────────

def build_snapshot(df_1m: pd.DataFrame, session_ts: pd.Timestamp) -> Model2022Snapshot:
    """
    Slice raw 1m data and resample into the three timeframes Model2022 needs.
    df_1m has a tz-naive UTC index.
    """
    d_naive = pd.Timestamp(session_ts.date())
    d = d_naive.tz_localize('UTC') if df_1m.index.tz is not None else d_naive

    df_3m = (
        df_1m.loc[d - pd.Timedelta(days=5) : d + pd.Timedelta(days=1)]
        .resample('3min').agg({'open': 'first', 'high': 'max', 'low': 'min',
                               'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    df_15m = (
        df_1m.loc[d - pd.Timedelta(days=14) : d + pd.Timedelta(days=1)]
        .resample('15min').agg({'open': 'first', 'high': 'max', 'low': 'min',
                                'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    df_daily = (
        df_1m.loc[d - pd.Timedelta(days=45) : d - pd.Timedelta(minutes=1)]
        .resample('D').agg({'open': 'first', 'high': 'max', 'low': 'min',
                            'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )
    return Model2022Snapshot(
        df_3m=df_3m, df_15m=df_15m, df_daily=df_daily, session_date=session_ts,
    )


# ─── Plotly report adapter ───────────────────────────────────────────────────

C_ENTRY, C_STOP, C_TARGET = '#1f77b4', '#c0392b', '#1a8a4a'
C_FVG, C_SWEEP, C_MSS, C_BIAS = '#f39c12', '#8e44ad', '#16a085', '#7f8c8d'


def _window(df: pd.DataFrame, lo: pd.Timestamp, hi: pd.Timestamp) -> pd.DataFrame:
    lo = localize_to(lo, df.index)
    hi = localize_to(hi, df.index)
    return df.loc[lo:hi]


def trade_panels(snap: Model2022Snapshot, session_ts: pd.Timestamp) -> dict:
    """Windowed candlestick frames for the three timeframes the model used."""
    d = pd.Timestamp(session_ts.date())

    # df_daily ends before the session day; append the session day bar from 3m
    session_day_bar = (
        snap.df_3m
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
        '3m':    _window(snap.df_3m,  d, d + pd.Timedelta(days=1)),
    }


def signal_to_marks(signal: dict, fill: dict, exit_info: dict) -> list:
    """Translate a Model2022 signal into report overlays."""
    direction = signal['direction']
    marks = []

    # — Entry / Stop / Target (default on) —
    g = 'Entry/Stop/Target'
    marks += [
        Mark('level',  g, '3m', f"Entry {signal['entry']:.2f}",  C_ENTRY,  price=signal['entry']),
        Mark('level',  g, '3m', f"Stop {signal['stop']:.2f}",    C_STOP,   dash='dash', price=signal['stop']),
        Mark('level',  g, '3m', f"Target {signal['target']:.2f}", C_TARGET, dash='dash', price=signal['target']),
        Mark('marker', g, '3m', "Fill", C_ENTRY,
             time=fill['fill_time'], price=fill['fill_price'], symbol='circle'),
    ]
    if exit_info:
        col = (C_TARGET if exit_info['exit_reason'] == 'target'
               else C_STOP if exit_info['exit_reason'] == 'stop' else C_BIAS)
        marks.append(Mark('marker', g, '3m', f"Exit ({exit_info['exit_reason']})", col,
                          time=exit_info['exit_time'], price=exit_info['exit_price'], symbol='x'))

    # — FVG zone (default on) —
    if signal.get('fvg_top') is not None:
        marks.append(Mark('zone', 'FVG', '3m', "FVG", C_FVG,
                          y0=signal['fvg_bottom'], y1=signal['fvg_top'],
                          t0=signal['entry_time'],
                          t1=(exit_info['exit_time'] if exit_info else None)))

    # — Sweep: pool level + opening range box + touch markers (default off) —
    if signal.get('sweep_time') is not None:
        lbl = f"Sweep {signal.get('swept_pool') or ''}".strip()
        marks.append(Mark('marker', 'Sweep', '3m', lbl, C_SWEEP,
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
            t0 = cluster.get('range_start')
            t1 = cluster.get('range_end')
            if t0 is not None and t1 is not None:
                marks.append(Mark('zone', 'Sweep', '3m', 'Opening Range', C_SWEEP,
                                  y0=or_low, y1=or_high, t0=t0, t1=t1, default_on=True))
            for ts in cluster.get('timestamps', []):
                marks.append(Mark('marker', 'Sweep', '3m', f"Pool: {source} {price:.2f}",
                                  C_SWEEP, time=ts, price=price,
                                  symbol='diamond', default_on=True))
        elif source in ('PDH', 'PDL'):
            for ts in cluster.get('timestamps', []):
                marks.append(Mark('marker', 'Sweep', 'daily', f"Pool: {source} {price:.2f}",
                                  C_SWEEP, time=ts, price=price,
                                  symbol='diamond', default_on=True))
        else:
            for ts in cluster.get('timestamps', []):
                marks.append(Mark('marker', 'Sweep', '15m', f"Pool: {source} {price:.2f}",
                                  C_SWEEP, time=ts, price=price,
                                  symbol='diamond', default_on=True))

    # — MSS (default off) —
    if signal.get('bms_time') is not None:
        sym = 'triangle-down' if direction == 'short' else 'triangle-up'
        marks.append(Mark('marker', 'MSS', '3m', f"MSS {signal['bms_swing_level']:.2f}", C_MSS,
                          time=signal['bms_time'], price=signal['bms_swing_level'],
                          symbol=sym, default_on=True))
        marks.append(Mark('level', 'MSS', '3m', "MSS swing", C_MSS, dash='dot',
                          price=signal['bms_swing_level'], default_on=True))

    return marks


# ─── Main loop ───────────────────────────────────────────────────────────────

def run_backtest():
    start_dt     = pd.Timestamp(START_DATE)
    warmup_start = start_dt - pd.Timedelta(weeks=WARMUP_WEEKS)
    weeks_needed = int((pd.Timestamp.now() - warmup_start).days / 7) + 4

    print(f"Loading NQ 1m data (~{weeks_needed} weeks from {warmup_start.date()})...")
    loader = DataLoader(timeframe='1min', weeks=weeks_needed, data_dir=DATA_DIR)
    df_1m  = loader.read_NQ()
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
    print(f"  {len(trading_days)} trading days  {trading_days[0]} → {trading_days[-1]}\n")

    model      = Model2022()
    trade_log  = []
    viz_trades = []
    n_signals  = 0
    n_no_fill  = 0
    n_errors   = 0

    for i, day in enumerate(trading_days):
        session_ts = pd.Timestamp(day)
        try:
            snap   = build_snapshot(df_1m, session_ts)
            signal = model.generate_signal(snap)
        except Exception as exc:
            n_errors += 1
            print(f"  ERROR {day}: {exc}")
            continue

        if not signal['actionable']:
            continue
        n_signals += 1

        fill = simulate_fill(snap.df_3m, signal, session_ts, EOD_EXIT_HOUR)
        if fill is None:
            n_no_fill += 1
            continue

        exit_info = simulate_exit(snap.df_3m, signal, fill, session_ts, EOD_EXIT_HOUR)
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

        viz_trades.append(TradeViz(
            label=f"{day}  {signal['direction'].upper()}  ${pnl_usd:,.0f}",
            panels=trade_panels(snap, session_ts),
            marks=signal_to_marks(signal, fill, exit_info),
            pnl=pnl_usd,
        ))

        if (i + 1) % 50 == 0:
            pnl_so_far = sum(t['pnl_usd'] for t in trade_log)
            print(f"  Day {i+1:>3}/{len(trading_days)}  "
                  f"signals={n_signals}  trades={len(trade_log)}  "
                  f"P&L=${pnl_so_far:,.0f}")

    print(f"\n── Summary ──────────────────────────────────────────")
    print(f"  Days evaluated : {len(trading_days)}")
    print(f"  Signals fired  : {n_signals}")
    print(f"  No-fill (limit never reached): {n_no_fill}")
    print(f"  Filled trades  : {len(trade_log)}")
    print(f"  Errors         : {n_errors}")

    if not trade_log:
        print("\nNo trades executed — nothing to report.")
        return

    trades = pd.DataFrame(trade_log)

    log_path = os.path.join(OUT_DIR, 'fvg_sweep_nq_trades.csv')
    trades.to_csv(log_path, index=False)
    print(f"\nTrade log → {log_path}")

    stats = compute_stats(trades)
    print_stats(stats, f'FVG Sweep — NQ NY Session {START_DATE}→')

    trades['month'] = pd.to_datetime(trades['session_date']).dt.to_period('M')
    print(f"  {'Month':<10} {'Trades':>6}  {'Wins':>4}  {'P&L pts':>9}  {'P&L $':>9}")
    print(f"  {'-'*45}")
    for month, grp in trades.groupby('month'):
        w = (grp['exit_reason'] == 'target').sum()
        print(f"  {str(month):<10} {len(grp):>6}  {w:>4}  "
              f"{grp['pnl_pts'].sum():>9.1f}  {grp['pnl_usd'].sum():>9,.0f}")

    chart_path = os.path.join(OUT_DIR, 'fvg_sweep_nq_equity.png')
    plot_equity_curve(
        trades, chart_path,
        title=f'FVG Sweep — NQ NY Session {START_DATE}→  (1 contract, $20/pt)',
    )

    report_stats = {
        'Trades':          stats['total_trades'],
        'Win rate':        f"{stats['win_rate']}%  ({stats['wins']}W / {stats['losses']}L / {stats['eods']} EOD)",
        'Total P&L':       f"${stats['total_pnl_usd']:,.2f}  ({stats['total_pnl_pts']:.1f} pts)",
        'Avg R:R (setup)': stats['avg_rr'],
        'Profit factor':   stats['profit_factor'],
        'Max drawdown':    f"${stats['max_dd_usd']:,.2f}",
        'Sharpe':          stats['sharpe_ratio'],
    }
    report_path = os.path.join(OUT_DIR, 'fvg_sweep_nq_report.html')
    build_report(
        trades=viz_trades,
        panel_order=['daily', '15m', '3m'],
        out_path=report_path,
        title=f'ICT 2022 Model — NQ  {START_DATE}→',
        equity=trades['pnl_usd'].cumsum(),
        stats=report_stats,
    )
    print(f"Interactive report → {report_path}")


if __name__ == '__main__':
    run_backtest()
