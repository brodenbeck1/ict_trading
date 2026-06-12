#!/usr/bin/env python3
"""
FVG Sweep Trade Visualizer
===========================

Plots individual trades on a 2m candlestick chart with each rule in the
checklist labeled and annotated.

Usage:
  python3 plot_trades.py                   # plots first 12 filled trades
  python3 plot_trades.py --date 2025-03-14 # plots one specific session
  python3 plot_trades.py --n 20            # plots first N trades
  python3 plot_trades.py --all             # plots every trade (slow)
"""

import os
import sys
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

from ict import DataLoader, Model2022
from fvg_sweep_backtest import build_snapshot, simulate_fill, simulate_exit, START_DATE

DATA_DIR   = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))
TRADES_CSV = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results/fvg_sweep_nq/fvg_sweep_nq_trades.csv'))
OUT_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), '../results/fvg_sweep_nq/charts'))

NQ_DOLLARS_PER_POINT = 20.0

# Chart window in NY time
CHART_START_NY = '07:00'
CHART_END_NY   = '14:00'


# ─── Candlestick Drawing ──────────────────────────────────────────────────────

def _draw_candles(ax, df: pd.DataFrame):
    """Draw OHLC candlesticks on ax. df index must be tz-aware (NY) or positional."""
    width = 0.6   # bar width in x-units (index positions)
    xs = range(len(df))

    for i, (ts, row) in enumerate(df.iterrows()):
        bull = row['close'] >= row['open']
        color = '#26a69a' if bull else '#ef5350'
        body_lo = min(row['open'], row['close'])
        body_hi = max(row['open'], row['close'])

        # Wick
        ax.add_line(Line2D([i, i], [row['low'], row['high']],
                            color=color, linewidth=0.8, zorder=2))
        # Body
        ax.add_patch(mpatches.FancyBboxPatch(
            (i - width / 2, body_lo), width, max(body_hi - body_lo, 0.01),
            boxstyle='square,pad=0', facecolor=color,
            edgecolor=color, linewidth=0.5, zorder=3,
        ))

    ax.set_xlim(-1, len(df))
    ax.set_ylim(df['low'].min() - 10, df['high'].max() + 10)
    ax.autoscale_view()

    # X-axis: show HH:MM labels every ~30 bars (~60 min on 2m)
    tick_step = max(1, len(df) // 10)
    tick_positions = list(range(0, len(df), tick_step))
    tick_labels = []
    for pos in tick_positions:
        ts = df.index[pos]
        ny = ts.tz_convert('America/New_York') if ts.tzinfo else ts
        tick_labels.append(ny.strftime('%H:%M'))
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=7)


def _ts_to_x(df: pd.DataFrame, ts: pd.Timestamp) -> float | None:
    """Convert a timestamp to a chart x position (index in df)."""
    # Normalize both to same tz
    idx = df.index
    if idx.tz is not None and ts.tz is None:
        ts = ts.tz_localize(idx.tz)
    elif idx.tz is None and ts.tz is not None:
        ts = ts.replace(tzinfo=None)

    # Find nearest bar (within 3 bars)
    diffs = abs(idx - ts)
    nearest_pos = diffs.argmin()
    if diffs[nearest_pos] <= pd.Timedelta(minutes=4):
        return float(nearest_pos)
    return None


# ─── Single Trade Plot ────────────────────────────────────────────────────────

def plot_trade(df_1m: pd.DataFrame, session_date: pd.Timestamp,
               signal: dict, fill: dict | None, exit_info: dict | None,
               pnl_usd: float | None, out_path: str):

    # Build 2m chart window: CHART_START_NY → CHART_END_NY on session_date
    date_str   = str(session_date.date())
    start_ny   = pd.Timestamp(f'{date_str} {CHART_START_NY}', tz='America/New_York')
    end_ny     = pd.Timestamp(f'{date_str} {CHART_END_NY}', tz='America/New_York')
    start_utc  = start_ny.tz_convert('UTC')
    end_utc    = end_ny.tz_convert('UTC')

    # Slice 1m → resample 2m for chart
    if df_1m.index.tz is None:
        s, e = start_utc.replace(tzinfo=None), end_utc.replace(tzinfo=None)
    else:
        s, e = start_utc, end_utc

    raw = df_1m.loc[s:e]
    if len(raw) < 5:
        print(f"  Skipping {date_str} — not enough chart bars")
        return

    chart_df = (raw
        .resample('2min').agg({'open': 'first', 'high': 'max',
                               'low': 'min', 'close': 'last'})
        .dropna(subset=['close']))

    if len(chart_df) < 5:
        print(f"  Skipping {date_str} — chart df too short after resample")
        return

    direction = signal['direction']
    color_long  = '#26a69a'
    color_short = '#ef5350'
    dir_color   = color_short if direction == 'short' else color_long

    fig, ax = plt.subplots(figsize=(16, 8))
    _draw_candles(ax, chart_df)

    def hline(price, color, ls, lw, label, y_offset=0, x_pct=(0.0, 1.0), fontsize=8):
        x0 = x_pct[0] * len(chart_df)
        x1 = x_pct[1] * len(chart_df)
        ax.hlines(price, x0, x1, colors=color, linestyles=ls, linewidth=lw, zorder=4)
        ax.text(x1 + 0.3, price + y_offset, label,
                va='center', ha='left', fontsize=fontsize,
                color=color, fontweight='bold')

    def vline(ts, color, ls, lw, label, y_frac=0.98):
        x = _ts_to_x(chart_df, ts)
        if x is None:
            return
        y_min, y_max = ax.get_ylim()
        ax.axvline(x, color=color, linestyle=ls, linewidth=lw, zorder=5, alpha=0.7)
        ax.text(x, y_min + (y_max - y_min) * y_frac, label,
                va='top', ha='center', fontsize=7, color=color,
                rotation=90, fontweight='bold')

    tick = (chart_df['high'].max() - chart_df['low'].min()) * 0.01  # 1% range

    # ── Rule ① — REH/REL cluster ──────────────────────────────────────────
    reh = signal.get('reh_price')
    if reh:
        ax.axhline(reh, color='#9c27b0', linestyle='--', linewidth=1.2,
                   zorder=4, alpha=0.85)
        ax.text(0.5, reh + tick, '① REH/REL cluster', va='bottom', ha='center',
                fontsize=7.5, color='#9c27b0', fontweight='bold',
                transform=ax.get_yaxis_transform())

    # ── Rule ② — Stop hunt (sweep) ────────────────────────────────────────
    sweep_ts = signal.get('sweep_time')
    sweep_x  = _ts_to_x(chart_df, sweep_ts) if sweep_ts else None
    if sweep_x is not None:
        sweep_bar = chart_df.iloc[int(sweep_x)]
        marker_y  = sweep_bar['high'] + tick * 2 if direction == 'short' else sweep_bar['low'] - tick * 2
        va        = 'bottom' if direction == 'short' else 'top'
        arrow_dy  = tick * 3 if direction == 'short' else -tick * 3
        ax.annotate('② Stop\n   hunt',
                    xy=(sweep_x, sweep_bar['high'] if direction == 'short' else sweep_bar['low']),
                    xytext=(sweep_x, marker_y + arrow_dy),
                    arrowprops=dict(arrowstyle='->', color='#ff9800', lw=1.5),
                    fontsize=7.5, color='#ff9800', fontweight='bold',
                    ha='center', va=va)

    # ── Rule ③ — BMS ──────────────────────────────────────────────────────
    bms_ts    = signal.get('bms_time')
    bms_level = signal.get('bms_swing_level')
    bms_x     = _ts_to_x(chart_df, bms_ts) if bms_ts else None
    if bms_x is not None and bms_level:
        ax.scatter([bms_x], [bms_level], marker='D', s=60, color='#2196f3',
                   zorder=6, label='BMS')
        ax.text(bms_x + 0.5, bms_level + tick * 1.5, '③ BMS',
                va='bottom', ha='left', fontsize=7.5, color='#2196f3', fontweight='bold')

    # ── Rule ④ — FVG zone ─────────────────────────────────────────────────
    fvg_top = signal.get('fvg_top')
    fvg_bot = signal.get('fvg_bottom')
    if fvg_top and fvg_bot:
        fvg_x = _ts_to_x(chart_df, signal['entry_time']) if signal.get('entry_time') else None
        if fvg_x is not None:
            zone_start = max(0, int(fvg_x) - 1)
            zone_end   = min(len(chart_df), int(fvg_x) + 4)
            ax.fill_between(range(zone_start, zone_end),
                            fvg_bot, fvg_top,
                            alpha=0.25, color='#ffeb3b', zorder=2,
                            label='FVG zone')
            ax.text(zone_start + 0.3, (fvg_top + fvg_bot) / 2,
                    '④ FVG', va='center', ha='left',
                    fontsize=7.5, color='#f57f17', fontweight='bold')

    # ── Rule ⑤ — Entry limit ──────────────────────────────────────────────
    entry = signal['entry']
    hline(entry, dir_color, '-', 1.5, f'⑤ Entry  {entry:.2f}',
          y_offset=tick, x_pct=(0.4, 0.98))

    # ── Rule ⑥ — Stop ────────────────────────────────────────────────────
    stop = signal['stop']
    hline(stop, '#ef5350', '--', 1.2, f'⑥ Stop  {stop:.2f}',
          y_offset=tick, x_pct=(0.4, 0.98))

    # ── Rule ⑦ — Target ──────────────────────────────────────────────────
    target = signal['target']
    hline(target, '#26a69a', '--', 1.2, f'⑦ Target  {target:.2f}',
          y_offset=tick, x_pct=(0.4, 0.98))

    # Session midpoint (context line)
    mid = signal.get('session_midpoint')
    if mid:
        ax.axhline(mid, color='gray', linestyle=':', linewidth=0.8, alpha=0.6, zorder=1)
        ax.text(0.02, mid + tick * 0.5, 'Session 50%',
                va='bottom', fontsize=6.5, color='gray',
                transform=ax.get_yaxis_transform())

    def highlight_candle(x_pos, bar, border_color, label, label_above=True):
        """Draw a thick colored border around a candle body and annotate it."""
        if x_pos is None:
            return
        x_pos = int(round(x_pos))
        if x_pos < 0 or x_pos >= len(chart_df):
            return
        body_lo = min(bar['open'], bar['close'])
        body_hi = max(bar['open'], bar['close'])
        height  = max(body_hi - body_lo, 0.5)
        width   = 0.7
        rect = mpatches.FancyBboxPatch(
            (x_pos - width / 2, body_lo), width, height,
            boxstyle='square,pad=0',
            facecolor='none', edgecolor=border_color,
            linewidth=2.5, zorder=7,
        )
        ax.add_patch(rect)
        y_anchor = body_hi if label_above else body_lo
        dy = tick * 2.5 if label_above else -tick * 2.5
        va = 'bottom' if label_above else 'top'
        ax.annotate(
            label,
            xy=(x_pos, y_anchor),
            xytext=(x_pos, y_anchor + dy),
            arrowprops=dict(arrowstyle='->', color=border_color, lw=1.2),
            fontsize=7.5, color=border_color, fontweight='bold',
            ha='center', va=va, zorder=8,
        )

    # ── Fill — highlight entry candle ─────────────────────────────────────
    if fill:
        vline(fill['fill_time'], dir_color, ':', 1.5, 'FILLED', y_frac=0.02)
        fill_x = _ts_to_x(chart_df, fill['fill_time']
                           if not isinstance(fill['fill_time'], str)
                           else pd.Timestamp(fill['fill_time']))
        if fill_x is not None:
            bar = chart_df.iloc[int(round(fill_x))]
            label_above = direction == 'long'
            highlight_candle(fill_x, bar, dir_color, 'ENTRY', label_above=label_above)

    # ── Exit — highlight exit candle ──────────────────────────────────────
    if exit_info:
        exit_ts = exit_info['exit_time']
        if isinstance(exit_ts, str):
            exit_ts = pd.Timestamp(exit_ts)
        exit_x = _ts_to_x(chart_df, exit_ts)
        reason = exit_info['exit_reason'].upper()
        ex_color = '#26a69a' if reason == 'TARGET' else ('#ef5350' if reason == 'STOP' else 'darkorange')

        vline(exit_ts, ex_color, '--', 1.5, f'EXIT ({reason})', y_frac=0.15)

        if exit_x is not None:
            bar = chart_df.iloc[int(round(exit_x))]
            # exit label: above for stops on shorts, below for targets on shorts
            label_above = (direction == 'short' and reason == 'STOP') or \
                          (direction == 'long' and reason == 'TARGET')
            highlight_candle(exit_x, bar, ex_color, f'EXIT\n{reason}', label_above=label_above)

        if pnl_usd is not None:
            sign = '+' if pnl_usd >= 0 else ''
            ax.text(0.98, 0.97, f'{sign}${pnl_usd:,.0f}',
                    transform=ax.transAxes, ha='right', va='top',
                    fontsize=14, fontweight='bold',
                    color='#26a69a' if pnl_usd >= 0 else '#ef5350')

    # ── Title & Formatting ───────────────────────────────────────────────
    risk_pts  = abs(signal['stop'] - signal['entry'])
    rew_pts   = abs(signal['target'] - signal['entry'])
    rr        = rew_pts / risk_pts if risk_pts else 0

    ax.set_title(
        f"FVG Sweep — NQ  {date_str}  |  {direction.upper()}  "
        f"risk={risk_pts:.1f}pts  reward={rew_pts:.1f}pts  R:R={rr:.1f}",
        fontsize=11, fontweight='bold', pad=10,
    )
    ax.set_ylabel('Price', fontsize=9)
    ax.grid(True, alpha=0.2, zorder=0)
    ax.set_facecolor('#111111' if False else '#fafafa')

    # Legend box for the checklist
    legend_items = [
        mpatches.Patch(color='#9c27b0', label='① REH/REL cluster'),
        mpatches.Patch(color='#ff9800', label='② Stop hunt (sweep)'),
        mpatches.Patch(color='#2196f3', label='③ BMS (break of structure)'),
        mpatches.Patch(color='#ffeb3b', alpha=0.5, label='④ FVG zone'),
        mpatches.Patch(color=dir_color, label=f'⑤ Entry limit ({direction})'),
        mpatches.Patch(color='#ef5350', label='⑥ Stop'),
        mpatches.Patch(color='#26a69a', label='⑦ Target'),
    ]
    ax.legend(handles=legend_items, loc='upper left', fontsize=7.5,
              framealpha=0.9, ncol=1)

    fig.subplots_adjust(left=0.06, right=0.88, top=0.93, bottom=0.07)
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved → {out_path}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', default=None, help='Plot one session (YYYY-MM-DD)')
    parser.add_argument('--n',    type=int, default=12, help='Number of trades to plot (default 12)')
    parser.add_argument('--all',  action='store_true',  help='Plot all trades')
    args = parser.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    trades = pd.read_csv(TRADES_CSV)
    if args.date:
        trades = trades[trades['session_date'] == args.date]
        if len(trades) == 0:
            print(f"No trade found for {args.date}")
            return
    elif not args.all:
        trades = trades.head(args.n)

    print(f"Plotting {len(trades)} trade(s)...")
    print(f"Loading NQ 1m data...")
    loader = DataLoader(timeframe='1min', weeks=64, data_dir=DATA_DIR)
    df_1m  = loader.read_NQ()

    model = Model2022()

    for _, row in trades.iterrows():
        session_ts = pd.Timestamp(row['session_date'])
        print(f"\n  {row['session_date']}  {row['direction'].upper()}")

        try:
            snap   = build_snapshot(df_1m, session_ts)
            signal = model.generate_signal(snap)
        except Exception as exc:
            print(f"  ERROR re-running model: {exc}")
            continue

        if not signal['actionable']:
            print(f"  Signal no longer actionable (data may differ) — skipping")
            continue

        fill      = simulate_fill(snap.df_2m, signal, session_ts)
        exit_info = simulate_exit(snap.df_2m, signal, fill, session_ts) if fill else None
        pnl_usd   = float(row['pnl_usd']) if fill else None

        out_path = os.path.join(OUT_DIR, f"{row['session_date']}_{row['direction']}.png")
        plot_trade(df_1m, session_ts, signal, fill, exit_info, pnl_usd, out_path)

    print(f"\nDone. Charts saved to {OUT_DIR}/")


if __name__ == '__main__':
    main()
