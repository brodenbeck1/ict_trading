"""
DXY Weekly — Swing High Classification Chart

For each swing high, classify as:
  - no_liquidity : already took the prior swing high (high[i] > prior_swing_high)
  - hpfs         : did NOT take the prior swing high — valid DOL candidate

Equal highs (high[i] == prior) are NOT disqualified — they count as HPFS
(relative equal highs = doubled-up liquidity, not consumed).

Usage: python charts/chart_dxy_swing_classification.py
Output: charts/dxy-weekly-bias/dxy-swing-classification-<start>.png
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

from ict.concepts.market_structure import SwingPointScanner

# ── palette ──────────────────────────────────────────────────────────────────
BG      = '#0d1117'
FG      = '#c9d1d9'
BULL_C  = '#3fb950'
BEAR_C  = '#f85149'
HPFS_C  = '#58a6ff'    # blue  — HPFS candidate (did NOT take prior high)
NOLIQ_C = '#f0883e'    # orange — no-liquidity (already took prior high)
LINE_A  = 0.55         # alpha for horizontal lines


def fetch_dxy_weekly(start: str, end: str) -> pd.DataFrame:
    raw = yf.download('DX-Y.NYB', start=start, end=end, interval='1wk',
                      auto_adjust=True, progress=False)
    raw.columns = [c[0].lower() if isinstance(c, tuple) else c.lower()
                   for c in raw.columns]
    raw.index = pd.to_datetime(raw.index)
    return raw.dropna()


def plot_candles(ax, df):
    w = 3.0
    for ts, row in df.iterrows():
        x = mdates.date2num(ts)
        o, h, l, c = float(row['open']), float(row['high']), float(row['low']), float(row['close'])
        color = BULL_C if c >= o else BEAR_C
        ax.plot([x, x], [l, h], color=color, lw=0.8, zorder=1)
        body_h = abs(c - o) or 0.01
        rect = Rectangle((x - w, min(o, c)), 2 * w, body_h,
                          facecolor=color, edgecolor=color, lw=0, zorder=2)
        ax.add_patch(rect)


def classify_swing_highs(swing_highs: pd.DataFrame) -> pd.DataFrame:
    """
    Given a DataFrame of swing highs (from SwingPointScanner), return the same
    rows with an added 'classification' column: 'hpfs' or 'no_liquidity'.

    Rule: if swing_high_price[i] > swing_high_price[i-1] → no_liquidity
          if swing_high_price[i] <= swing_high_price[i-1] → hpfs
    First swing high has no prior → hpfs by default.
    """
    rows = swing_highs[['swing_high_price']].copy()
    classifications = []
    prev = None
    for price in rows['swing_high_price']:
        if prev is None or price <= prev:
            classifications.append('hpfs')
        else:
            classifications.append('no_liquidity')
        prev = price
    rows['classification'] = classifications
    return rows


def plot_swing_high_lines(ax, classified, df_end_ts):
    """
    For each swing high draw a horizontal line extending to the right until
    price takes it (any later candle high > level), then dotted after.
    """
    end_num = mdates.date2num(df_end_ts)
    all_highs = classified.index  # timestamps of swing highs

    first_hpfs = first_noliq = True

    for ts, row in classified.iterrows():
        level = row['swing_high_price']
        color = HPFS_C if row['classification'] == 'hpfs' else NOLIQ_C
        label_hpfs   = 'HPFS candidate' if first_hpfs   and row['classification'] == 'hpfs'         else '_'
        label_noliq  = 'No-liquidity'   if first_noliq  and row['classification'] == 'no_liquidity' else '_'
        label = label_hpfs if row['classification'] == 'hpfs' else label_noliq

        if row['classification'] == 'hpfs':
            first_hpfs = False
        else:
            first_noliq = False

        x_start = mdates.date2num(ts)

        # find when it gets taken (first later candle with high > level)
        future = classified.index[classified.index > ts]
        # also check raw df highs (not just swing highs)
        # we need the full df — pass it in via closure
        taken_ts = _first_raid(level, ts)

        x_end = mdates.date2num(taken_ts) if taken_ts is not None else end_num

        ax.hlines(level, x_start, x_end, colors=color, linewidths=1.1,
                  linestyles='solid', alpha=LINE_A, zorder=3, label=label)

        if taken_ts is not None and x_end < end_num:
            ax.hlines(level, x_end, end_num, colors=color, linewidths=0.5,
                      linestyles='dotted', alpha=0.35, zorder=2)
            ax.scatter([x_end], [level], marker='x', color=color,
                       s=60, linewidths=1.3, alpha=0.8, zorder=5)

        # marker at the swing high
        ax.scatter([x_start], [level], marker='^' if row['classification'] == 'hpfs' else 'v',
                   color=color, s=45, zorder=6, alpha=0.9)


# module-level df reference for the raid lookup closure
_df_global: pd.DataFrame = None


def _first_raid(level: float, from_ts: pd.Timestamp):
    future = _df_global[_df_global.index > from_ts]
    taken = future[future['high'] > level]
    return taken.index[0] if len(taken) else None


def main():
    global _df_global
    start, end = '2021-06-01', '2023-06-30'
    df = fetch_dxy_weekly(start, end)
    _df_global = df
    print(f"Loaded {len(df)} weekly DXY bars ({df.index[0].date()} → {df.index[-1].date()})")

    scanner = SwingPointScanner(df, lookback=1)
    scanner.identify_swings()

    swing_highs = scanner.swing_highs[['swing_high_price']].dropna()
    classified  = classify_swing_highs(swing_highs)

    n_hpfs   = (classified['classification'] == 'hpfs').sum()
    n_noliq  = (classified['classification'] == 'no_liquidity').sum()
    print(f"\nSwing highs — HPFS candidates: {n_hpfs}  |  No-liquidity: {n_noliq}")
    for ts, row in classified.iterrows():
        tag = '✓ HPFS' if row['classification'] == 'hpfs' else '✗ no-liq'
        print(f"  {ts.date()}  {row['swing_high_price']:.2f}  {tag}")

    # ── plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(16, 7), facecolor=BG)
    ax.set_facecolor(BG)

    plot_candles(ax, df)
    plot_swing_high_lines(ax, classified, df.index[-1])

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
    ax.set_title(
        f'DXY Weekly — Swing High Classification  ({start} → {end})\n'
        f'Blue ▲ = HPFS candidate (valid DOL)   Orange ▽ = No-liquidity (already swept)',
        color=FG, fontsize=11, pad=10
    )
    ax.legend(facecolor='#161b22', edgecolor='#30363d',
              labelcolor=FG, fontsize=9, loc='upper left')

    out_dir  = os.path.join(os.path.dirname(__file__), 'dxy-weekly-bias')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir,
                            f'dxy-swing-classification-{pd.Timestamp(start).strftime("%Y-%m-%d")}.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f"\nSaved → {out_path}")
    return out_path


if __name__ == '__main__':
    path = main()
    os.system(f'open "{path}"')
