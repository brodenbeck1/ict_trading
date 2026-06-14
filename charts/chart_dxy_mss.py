"""
DXY Weekly Bias Chart — HPFS pools + MSS example.

Uses find_hpfs() (LTC → inside-body scan) to mark HPFS levels, not the
DOL pool-validity classifier.

Usage: python charts/chart_dxy_mss.py
Output: charts/dxy-weekly-bias/dxy-weekly-bias-DXY-<start_date>.png
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import yfinance as yf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ict.concepts.hpfs import find_hpfs
from ict.concepts.market_structure import detect_mss

# ── palette ──────────────────────────────────────────────────────────────────
BG     = '#0d1117'
FG     = '#c9d1d9'
BULL_C = '#3fb950'   # green — bullish candles
BEAR_C = '#f85149'   # red   — bearish candles
HPFS_B = '#58a6ff'   # blue  — bearish HPFS (sell-side highs)
HPFS_G = '#39d353'   # green — bullish HPFS (buy-side lows)
LTC_C  = '#bc8cff'   # purple — LTC marker
MSS_C  = '#e3b341'   # gold  — MSS
RAID_C = '#e3b341'   # gold  — raid X


def fetch_dxy_weekly(start: str, end: str) -> pd.DataFrame:
    raw = yf.download('DX-Y.NYB', start=start, end=end, interval='1wk',
                      auto_adjust=True, progress=False)
    raw.columns = [c[0].lower() if isinstance(c, tuple) else c.lower()
                   for c in raw.columns]
    raw.index = pd.to_datetime(raw.index)
    return raw.dropna()


def plot_candles(ax, df):
    w = 3.0  # half-width in matplotlib date units (days)
    for ts, row in df.iterrows():
        x = mdates.date2num(ts)
        o, h, l, c = float(row['open']), float(row['high']), float(row['low']), float(row['close'])
        color = BULL_C if c >= o else BEAR_C
        ax.plot([x, x], [l, h], color=color, lw=0.8, zorder=1)
        body_h = abs(c - o) or 0.01
        rect = Rectangle((x - w, min(o, c)), 2 * w, body_h,
                          facecolor=color, edgecolor=color, lw=0, zorder=2)
        ax.add_patch(rect)


def plot_hpfs_levels(ax, hpfs_df, color, end_ts, direction):
    """Draw each HPFS level: solid from hpfs_time → raid (or end), X at raid."""
    last_ts_num = mdates.date2num(end_ts)
    first = True
    for _, row in hpfs_df.iterrows():
        level     = row['hpfs_level']
        start_num = mdates.date2num(row['hpfs_time'])
        has_raid  = pd.notna(row['raid_time'])
        end_num   = mdates.date2num(row['raid_time']) if has_raid else last_ts_num

        # solid active portion
        ax.hlines(level, start_num, end_num, colors=color, linewidths=1.0,
                  linestyles='solid', zorder=4,
                  label=f'HPFS {"high" if direction == "bearish" else "low"}' if first else '_')
        first = False

        # dotted after raid
        if has_raid and end_num < last_ts_num:
            ax.hlines(level, end_num, last_ts_num, colors=color, linewidths=0.6,
                      linestyles='dotted', zorder=3)
            ax.scatter([end_num], [level], marker='x', color=RAID_C,
                       s=80, linewidths=1.5, zorder=6)

        # mark the LTC
        ax.scatter([mdates.date2num(row['ltc_time'])], [row['ltc_open']],
                   marker='|', color=LTC_C, s=60, linewidths=1.2, zorder=5)


def main():
    start, end = '2021-06-01', '2023-06-30'
    df = fetch_dxy_weekly(start, end)
    print(f"Loaded {len(df)} weekly DXY bars ({df.index[0].date()} → {df.index[-1].date()})")

    # ── HPFS detection ────────────────────────────────────────────────────────
    # Bearish HPFS (highs that formed after a sweep — potential sell-side draws)
    bear_rb = find_hpfs(df, 'bearish', ltc_type='rb')
    bear_ob = find_hpfs(df, 'bearish', ltc_type='ob')
    bear_all = pd.concat([bear_rb, bear_ob]).drop_duplicates('hpfs_time').sort_values('hpfs_time')

    # Bullish HPFS (lows that formed after a sweep — potential buy-side draws)
    bull_rb = find_hpfs(df, 'bullish', ltc_type='rb')
    bull_ob = find_hpfs(df, 'bullish', ltc_type='ob')
    bull_all = pd.concat([bull_rb, bull_ob]).drop_duplicates('hpfs_time').sort_values('hpfs_time')

    print(f"Bearish HPFS levels: {len(bear_all)}")
    for _, r in bear_all.iterrows():
        raided = r['raid_time'].date() if pd.notna(r['raid_time']) else 'active'
        print(f"  {r['hpfs_time'].date()}  level={r['hpfs_level']:.2f}  LTC={r['ltc_time'].date()}  raid={raided}")

    print(f"Bullish HPFS levels: {len(bull_all)}")
    for _, r in bull_all.iterrows():
        raided = r['raid_time'].date() if pd.notna(r['raid_time']) else 'active'
        print(f"  {r['hpfs_time'].date()}  level={r['hpfs_level']:.2f}  LTC={r['ltc_time'].date()}  raid={raided}")

    # ── MSS: find most recent bearish sweep (peak) + confirm MSS ─────────────
    # Pool = high of bar before the all-time-high; sweep bar = the peak itself.
    peak_ts  = df['high'].idxmax()
    peak_idx = df.index.get_loc(peak_ts)
    raid_ts    = df.index[peak_idx - 1] if peak_idx > 0 else None
    raid_level = float(df.loc[raid_ts, 'high']) if raid_ts is not None else None
    raid_bar   = peak_ts

    mss = detect_mss(df, direction='bearish', swing_lookback=2,
                     max_bars_after_sweep=30, sweep_time=raid_bar)

    if raid_level:
        print(f"\nBuy-side pool raided: {raid_level:.2f} @ {raid_ts.date()}  peak @ {raid_bar.date()}")
    if mss:
        print(f"MSS confirmed: broke {mss['broken_level']:.2f} @ {mss['break_time'].date()}")

    # ── plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(16, 7), facecolor=BG)
    ax.set_facecolor(BG)

    plot_candles(ax, df)

    def ts2num(ts): return mdates.date2num(ts)

    # HPFS levels
    if not bear_all.empty:
        plot_hpfs_levels(ax, bear_all, HPFS_B, df.index[-1], 'bearish')
    if not bull_all.empty:
        plot_hpfs_levels(ax, bull_all, HPFS_G, df.index[-1], 'bullish')

    # Raided buy-side pool (the sweep into the peak)
    if raid_ts is not None:
        ax.hlines(raid_level, ts2num(raid_ts), ts2num(raid_bar),
                  colors=HPFS_B, linewidths=1.4, linestyles='solid', zorder=4,
                  label='Raided pool')
        ax.hlines(raid_level, ts2num(raid_bar), ts2num(df.index[-1]),
                  colors=HPFS_B, linewidths=0.7, linestyles='dotted', zorder=3)
        ax.scatter([ts2num(raid_bar)], [raid_level], marker='x', color=RAID_C,
                   s=130, linewidths=2.2, zorder=7, label='Raid (peak)')

    # MSS marker
    if mss:
        ax.scatter([ts2num(mss['break_time'])], [mss['broken_level']], marker='D',
                   color=MSS_C, s=110, zorder=8, label='MSS')
        ax.hlines(mss['broken_level'], ts2num(df.index[0]), ts2num(mss['break_time']),
                  colors=MSS_C, linewidths=0.6, linestyles='dotted', alpha=0.5)

    # LTC legend entry (already added inside plot_hpfs_levels)
    ax.scatter([], [], marker='|', color=LTC_C, s=60, label='LTC open')

    # ── cosmetics ─────────────────────────────────────────────────────────────
    for spine in ax.spines.values():
        spine.set_color('#30363d')
    ax.tick_params(colors=FG)
    ax.yaxis.tick_right()
    ax.set_ylabel('Price', color=FG, labelpad=8)
    ax.yaxis.set_label_position('right')
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.xticks(rotation=30, ha='right')
    ax.grid(axis='y', color='#21262d', linewidth=0.5)
    ax.set_title(f'DXY Weekly — HPFS (find_hpfs) + MSS  ({start} → {end})',
                 color=FG, fontsize=12, pad=10)
    ax.legend(facecolor='#161b22', edgecolor='#30363d',
              labelcolor=FG, fontsize=8, loc='upper left')

    # ── save ─────────────────────────────────────────────────────────────────
    out_dir  = os.path.join(os.path.dirname(__file__), 'dxy-weekly-bias')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'dxy-weekly-bias-DXY-{pd.Timestamp(start).strftime("%Y-%m-%d")}.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f"\nSaved → {out_path}")


if __name__ == '__main__':
    main()
