#!/usr/bin/env python3
"""
FVG Sweep Model Backtester — NQ NY Session
===========================================

Walk-forward backtest on NQ futures, NY session 8:30–11:00 AM.
One signal evaluated per trading day. Fixed 1 NQ contract ($20/pt).

Outputs:
  fvg_sweep_nq_trades.csv   — full trade log
  fvg_sweep_nq_equity.png   — equity curve + trade bar chart
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ict_library import DataLoader, FVGSweepModel, FVGSweepSnapshot

# ─── Config ──────────────────────────────────────────────────────────────────

NQ_DOLLARS_PER_POINT = 20.0    # NQ full contract
START_DATE     = '2024-11-01'  # backtest start date (inclusive)
WARMUP_WEEKS   = 14            # extra history before START_DATE for bias/REH warmup
EOD_EXIT_HOUR  = 16            # NY hour for EOD exit (16:00 = RTH close)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Data'))
OUT_DIR  = os.path.dirname(os.path.abspath(__file__))


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _to_ny(ts: pd.Timestamp) -> pd.Timestamp:
    """Convert a tz-naive UTC timestamp to America/New_York."""
    return ts.tz_localize('UTC').tz_convert('America/New_York')


def _eod_utc(session_date: pd.Timestamp, tz_aware: bool = False) -> pd.Timestamp:
    """Return EOD (16:00 NY) as UTC. tz_aware=True returns tz-aware, False returns tz-naive."""
    date_str = str(session_date.date())
    eod_ny = pd.Timestamp(f'{date_str} {EOD_EXIT_HOUR}:00:00', tz='America/New_York')
    eod = eod_ny.tz_convert('UTC')
    return eod if tz_aware else eod.replace(tzinfo=None)


def _localize_to(ts: pd.Timestamp, ref_index: pd.DatetimeIndex) -> pd.Timestamp:
    """Make ts tz-aware/naive to match ref_index tz."""
    if ref_index.tz is not None and ts.tz is None:
        return ts.tz_localize(ref_index.tz)
    if ref_index.tz is None and ts.tz is not None:
        return ts.replace(tzinfo=None)
    return ts


# ─── Snapshot Builder ────────────────────────────────────────────────────────

def build_snapshot(df_1m: pd.DataFrame, session_date: pd.Timestamp) -> FVGSweepSnapshot:
    """
    Slice raw 1m data and resample into the three timeframes FVGSweepModel needs.
    df_1m has a tz-naive UTC index.
    """
    # Build a UTC-aware anchor date (handles both tz-aware and tz-naive df_1m index)
    d_naive = pd.Timestamp(session_date.date())
    d = d_naive.tz_localize('UTC') if df_1m.index.tz is not None else d_naive

    # 2m: 5 days back + session day (BMS detection needs some pre-session context)
    df_2m = (
        df_1m.loc[d - pd.Timedelta(days=5) : d + pd.Timedelta(days=1)]
        .resample('2min').agg({'open': 'first', 'high': 'max', 'low': 'min',
                               'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )

    # 15m: 14 days back + session day (REH detection + target finding)
    df_15m = (
        df_1m.loc[d - pd.Timedelta(days=14) : d + pd.Timedelta(days=1)]
        .resample('15min').agg({'open': 'first', 'high': 'max', 'low': 'min',
                                'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )

    # Weekly: 10 weeks back (up to but not including session day — bias is pre-session)
    df_weekly = (
        df_1m.loc[d - pd.Timedelta(weeks=10) : d]
        .resample('W').agg({'open': 'first', 'high': 'max', 'low': 'min',
                            'close': 'last', 'volume': 'sum'})
        .dropna(subset=['close'])
    )

    return FVGSweepSnapshot(
        df_2m=df_2m,
        df_15m=df_15m,
        df_weekly=df_weekly,
        session_date=session_date,
    )


# ─── Fill Simulation ─────────────────────────────────────────────────────────

def simulate_fill(df_2m: pd.DataFrame, signal: dict, session_date: pd.Timestamp) -> dict | None:
    """
    Scan 2m bars after entry_time for a limit fill.
    Fill window: entry_time → EOD (16:00 NY).
    Short fills when high >= entry; long fills when low <= entry.
    Returns {'fill_time', 'fill_price'} or None.
    """
    entry_time  = _localize_to(signal['entry_time'], df_2m.index)
    entry_price = signal['entry']
    direction   = signal['direction']
    eod         = _eod_utc(session_date, tz_aware=(df_2m.index.tz is not None))

    df_fill = df_2m[(df_2m.index > entry_time) & (df_2m.index <= eod)]

    for ts, row in df_fill.iterrows():
        if direction == 'short' and row['high'] >= entry_price:
            return {'fill_time': ts, 'fill_price': entry_price}
        if direction == 'long' and row['low'] <= entry_price:
            return {'fill_time': ts, 'fill_price': entry_price}

    return None


# ─── Exit Simulation ─────────────────────────────────────────────────────────

def simulate_exit(df_2m: pd.DataFrame, signal: dict, fill: dict,
                  session_date: pd.Timestamp) -> dict:
    """
    From fill_time → EOD, find first target or stop hit.
    Falls back to EOD close price.
    Returns {'exit_time', 'exit_price', 'exit_reason'}.
    """
    direction  = signal['direction']
    target     = signal['target']
    stop       = signal['stop']
    fill_time  = _localize_to(fill['fill_time'], df_2m.index)
    eod        = _eod_utc(session_date, tz_aware=(df_2m.index.tz is not None))

    df_after = df_2m[(df_2m.index > fill_time) & (df_2m.index <= eod)]

    for ts, row in df_after.iterrows():
        if direction == 'short':
            if row['low'] <= target:
                return {'exit_time': ts, 'exit_price': target, 'exit_reason': 'target'}
            if row['high'] >= stop:
                return {'exit_time': ts, 'exit_price': stop, 'exit_reason': 'stop'}
        else:   # long
            if row['high'] >= target:
                return {'exit_time': ts, 'exit_price': target, 'exit_reason': 'target'}
            if row['low'] <= stop:
                return {'exit_time': ts, 'exit_price': stop, 'exit_reason': 'stop'}

    if len(df_after) > 0:
        last = df_after.iloc[-1]
        return {'exit_time': df_after.index[-1],
                'exit_price': float(last['close']),
                'exit_reason': 'eod'}

    return {'exit_time': fill_time, 'exit_price': fill['fill_price'], 'exit_reason': 'eod'}


def calc_pnl_pts(direction: str, entry: float, exit_price: float) -> float:
    return (entry - exit_price) if direction == 'short' else (exit_price - entry)


# ─── Statistics ──────────────────────────────────────────────────────────────

def compute_stats(trades: pd.DataFrame) -> dict:
    if len(trades) == 0:
        return {}

    pnl_pts = trades['pnl_pts']
    pnl_usd = trades['pnl_usd']

    wins   = trades[trades['exit_reason'] == 'target']
    losses = trades[trades['exit_reason'] == 'stop']
    eods   = trades[trades['exit_reason'].str.startswith('eod')]

    gross_wins   = wins['pnl_usd'].sum() if len(wins) else 0.0
    gross_losses = abs(losses['pnl_usd'].sum()) if len(losses) else 1e-9

    equity   = pnl_usd.cumsum()
    peak     = equity.cummax()
    max_dd   = float((equity - peak).min())

    # Sharpe on per-trade returns (annualized assuming ~252 trades/year approximation)
    daily_ret = trades.groupby('session_date')['pnl_usd'].sum()
    sharpe = float(daily_ret.mean() / daily_ret.std() * np.sqrt(252)) if len(daily_ret) > 1 else 0.0

    avg_rr = float(trades['reward_pts'].mean() / trades['risk_pts'].replace(0, np.nan).mean()) \
        if len(trades) else 0.0

    return {
        'total_trades':    len(trades),
        'total_pnl_usd':  round(float(pnl_usd.sum()), 2),
        'total_pnl_pts':  round(float(pnl_pts.sum()), 2),
        'win_rate':        round(len(wins) / len(trades) * 100, 1),
        'wins':            len(wins),
        'losses':          len(losses),
        'eods':            len(eods),
        'avg_win_pts':     round(float(wins['pnl_pts'].mean()), 2) if len(wins) else 0,
        'avg_loss_pts':    round(float(losses['pnl_pts'].mean()), 2) if len(losses) else 0,
        'avg_win_usd':     round(float(wins['pnl_usd'].mean()), 2) if len(wins) else 0,
        'avg_loss_usd':    round(float(losses['pnl_usd'].mean()), 2) if len(losses) else 0,
        'profit_factor':   round(gross_wins / gross_losses, 2),
        'avg_rr':          round(avg_rr, 2),
        'max_dd_usd':      round(max_dd, 2),
        'sharpe_ratio':    round(sharpe, 2),
    }


def print_stats(stats: dict, label: str = 'Results'):
    w = 52
    print(f"\n{'='*w}")
    print(f"  {label}")
    print(f"{'='*w}")
    if not stats:
        print("  No trades.")
        return
    print(f"  Total trades:    {stats['total_trades']}")
    print(f"  Win rate:        {stats['win_rate']}%  "
          f"({stats['wins']}W / {stats['losses']}L / {stats['eods']} EOD)")
    print(f"  Total P&L:       ${stats['total_pnl_usd']:>10,.2f}  ({stats['total_pnl_pts']:.1f} pts)")
    print(f"  Avg win:         {stats['avg_win_pts']:>6.1f} pts  (${stats['avg_win_usd']:,.2f})")
    print(f"  Avg loss:        {stats['avg_loss_pts']:>6.1f} pts  (${stats['avg_loss_usd']:,.2f})")
    print(f"  Avg R:R (setup): {stats['avg_rr']:.2f}")
    print(f"  Profit factor:   {stats['profit_factor']:.2f}")
    print(f"  Max drawdown:    ${stats['max_dd_usd']:>10,.2f}")
    print(f"  Sharpe ratio:    {stats['sharpe_ratio']:.2f}")
    print()


# ─── Equity Curve ────────────────────────────────────────────────────────────

def plot_equity_curve(trades: pd.DataFrame, path: str):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8),
                                   gridspec_kw={'height_ratios': [3, 1]})

    equity = trades['pnl_usd'].cumsum()
    xs = range(len(equity))

    ax1.plot(equity.values, color='royalblue', linewidth=1.5, zorder=3)
    ax1.axhline(0, color='black', linewidth=0.7, linestyle='--')
    ax1.fill_between(xs, equity.values, 0,
                     where=(equity.values >= 0), alpha=0.12, color='green', zorder=2)
    ax1.fill_between(xs, equity.values, 0,
                     where=(equity.values < 0), alpha=0.12, color='red', zorder=2)
    ax1.set_title(f'FVG Sweep — NQ NY Session {START_DATE}→ — Equity Curve (1 contract, $20/pt)',
                  fontsize=12)
    ax1.set_ylabel('Cumulative P&L (USD)')
    ax1.grid(True, alpha=0.25)

    colors = ['green' if r == 'target' else ('red' if r == 'stop' else 'darkorange')
              for r in trades['exit_reason']]
    ax2.bar(xs, trades['pnl_usd'], color=colors, alpha=0.8)
    ax2.axhline(0, color='black', linewidth=0.5)
    ax2.set_ylabel('Trade P&L (USD)')
    ax2.set_xlabel('Trade #')
    ax2.grid(True, alpha=0.25)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='green',     alpha=0.8, label='Target hit'),
        Patch(facecolor='red',       alpha=0.8, label='Stop hit'),
        Patch(facecolor='darkorange',alpha=0.8, label='EOD exit'),
    ]
    ax2.legend(handles=legend_elements, loc='upper left', fontsize=8)

    plt.tight_layout()
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Equity curve → {path}")


# ─── Main Loop ───────────────────────────────────────────────────────────────

def run_backtest():
    # Load all data: warmup weeks before START_DATE + everything after
    start_dt = pd.Timestamp(START_DATE)
    warmup_start = start_dt - pd.Timedelta(weeks=WARMUP_WEEKS)
    weeks_needed = int((pd.Timestamp.now() - warmup_start).days / 7) + 4

    print(f"Loading NQ 1m data (~{weeks_needed} weeks from {warmup_start.date()})...")
    loader = DataLoader(timeframe='1min', weeks=weeks_needed, data_dir=DATA_DIR)
    df_1m  = loader.read_NQ()
    print(f"  Loaded {len(df_1m):,} rows  {df_1m.index[0]} → {df_1m.index[-1]}")

    # Identify NY session trading days on or after START_DATE
    raw_idx_full = df_1m.index
    if raw_idx_full.tz is None:
        raw_idx_full = raw_idx_full.tz_localize('UTC')
    cutoff_utc = start_dt.tz_localize('UTC')
    df_bt = df_1m[raw_idx_full >= cutoff_utc] if df_1m.index.tz is not None else \
            df_1m[df_1m.index >= start_dt]

    # Convert to NY — handle both tz-aware and tz-naive index
    raw_idx = df_bt.index
    if raw_idx.tz is None:
        raw_idx = raw_idx.tz_localize('UTC')
    ny_idx = raw_idx.tz_convert('America/New_York')
    session_mask = (ny_idx.hour * 60 + ny_idx.minute >= 8 * 60 + 30) & \
                   (ny_idx.hour * 60 + ny_idx.minute <  11 * 60)
    trading_days = sorted(set(ny_idx.date[session_mask]))
    print(f"  {len(trading_days)} trading days  {trading_days[0]} → {trading_days[-1]}\n")

    model      = FVGSweepModel()
    trade_log  = []
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

        fill = simulate_fill(snap.df_2m, signal, session_ts)
        if fill is None:
            n_no_fill += 1
            continue

        exit_info = simulate_exit(snap.df_2m, signal, fill, session_ts)

        pnl_pts = calc_pnl_pts(signal['direction'], fill['fill_price'], exit_info['exit_price'])
        pnl_usd = round(pnl_pts * NQ_DOLLARS_PER_POINT, 2)

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

    # Save trade log
    log_path = os.path.join(OUT_DIR, 'fvg_sweep_nq_trades.csv')
    trades.to_csv(log_path, index=False)
    print(f"\nTrade log → {log_path}")

    # Overall stats
    stats = compute_stats(trades)
    print_stats(stats, f'FVG Sweep — NQ NY Session {START_DATE}→')

    # Monthly breakdown
    trades['month'] = pd.to_datetime(trades['session_date']).dt.to_period('M')
    print(f"  {'Month':<10} {'Trades':>6}  {'Wins':>4}  {'P&L pts':>9}  {'P&L $':>9}")
    print(f"  {'-'*45}")
    for month, grp in trades.groupby('month'):
        w = (grp['exit_reason'] == 'target').sum()
        print(f"  {str(month):<10} {len(grp):>6}  {w:>4}  "
              f"{grp['pnl_pts'].sum():>9.1f}  {grp['pnl_usd'].sum():>9,.0f}")

    # Equity curve
    chart_path = os.path.join(OUT_DIR, 'fvg_sweep_nq_equity.png')
    plot_equity_curve(trades, chart_path)


if __name__ == '__main__':
    run_backtest()
