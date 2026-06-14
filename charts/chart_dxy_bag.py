"""
DXY Weekly — Break Away Gaps (BAG)

Shows all bullish and bearish BAGs on the DXY weekly chart:
  - BAG zone drawn as a shaded rectangle (FVG top/bottom)
  - Vertical tick at the no-liquidity swing point that was broken through
  - Lines stop at the bar where the zone is fully mitigated

Usage: python charts/chart_dxy_bag.py
Output: charts/dxy-weekly-bias/dxy-bag-<start>.png
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

from ict.concepts.break_away_gap import find_break_away_gaps, BreakAwayGap
from ict.concepts.market_structure import SwingPointScanner
from ict.concepts.pool_validity import classify_swing_liquidity

# ── palette ──────────────────────────────────────────────────────────────────
BG      = '#0d1117'
FG      = '#c9d1d9'
BULL_C  = '#3fb950'
BEAR_C  = '#f85149'
BAG_B_C = '#58a6ff'    # blue  — bullish BAG zone
BAG_S_C = '#f85149'    # red   — bearish BAG zone
SWEPT_C = '#f0883e'    # orange — no-liquidity swing level marker


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


def first_mitigation(bag: BreakAwayGap, df: pd.DataFrame) -> pd.Timestamp | None:
    """Return the first bar that closes through the far edge of the BAG zone."""
    future = df[df.index > bag.fvg.timestamp]
    if bag.fvg.direction == 'bullish':
        # invalidated by close below bottom
        hit = future[future['close'] < bag.fvg.bottom]
    else:
        # invalidated by close above top
        hit = future[future['close'] > bag.fvg.top]
    return hit.index[0] if len(hit) else None


def plot_bags(ax, bags: list[BreakAwayGap], df: pd.DataFrame, end_ts: pd.Timestamp,
              color: str, direction: str, first_label: str):
    end_num = mdates.date2num(end_ts)
    first = True
    for bag in bags:
        fvg = bag.fvg
        x_start = mdates.date2num(fvg.timestamp)

        mit_ts = first_mitigation(bag, df)
        x_end  = mdates.date2num(mit_ts) if mit_ts is not None else end_num

        zone_h = fvg.top - fvg.bottom
        rect = Rectangle((x_start, fvg.bottom), x_end - x_start, zone_h,
                          facecolor=color, edgecolor=color,
                          alpha=0.18, lw=0, zorder=3)
        ax.add_patch(rect)

        # outline while active
        ax.hlines([fvg.top, fvg.bottom], x_start, x_end,
                  colors=color, linewidths=0.9, linestyles='solid', alpha=0.6, zorder=4,
                  label=first_label if first else '_')
        first = False

        # dotted after mitigation
        if mit_ts is not None and x_end < end_num:
            ax.hlines([fvg.top, fvg.bottom], x_end, end_num,
                      colors=color, linewidths=0.5, linestyles='dotted', alpha=0.3, zorder=3)

        # mark the BAG displacement bar
        ax.scatter([mdates.date2num(fvg.timestamp)],
                   [fvg.top if direction == 'bullish' else fvg.bottom],
                   marker='D', color=color, s=35, zorder=7, alpha=0.9)


def main():
    start, end = '2021-06-01', '2023-06-30'
    df = fetch_dxy_weekly(start, end)
    print(f"Loaded {len(df)} weekly DXY bars ({df.index[0].date()} → {df.index[-1].date()})")

    bull_bags = find_break_away_gaps(df, 'bullish', swing_lookback=1)
    bear_bags = find_break_away_gaps(df, 'bearish', swing_lookback=1)

    print(f"\nBullish BAGs: {len(bull_bags)}")
    for b in bull_bags:
        print(f"  {b.fvg.timestamp.date()}  zone={b.fvg.bottom:.2f}–{b.fvg.top:.2f}  "
              f"swept={b.swept_level:.2f}@{b.swept_ts.date()}")

    print(f"\nBearish BAGs: {len(bear_bags)}")
    for b in bear_bags:
        print(f"  {b.fvg.timestamp.date()}  zone={b.fvg.bottom:.2f}–{b.fvg.top:.2f}  "
              f"swept={b.swept_level:.2f}@{b.swept_ts.date()}")

    # ── all no-liquidity swings (regardless of whether a BAG formed) ──────────
    scanner = SwingPointScanner(df, lookback=1)
    scanner.identify_swings()

    sh = scanner.swing_highs[['swing_high_price']].dropna()
    no_liq_highs = classify_swing_liquidity(sh, 'high')
    no_liq_highs = no_liq_highs[no_liq_highs['classification'] == 'no_liquidity']

    sl = scanner.swing_lows[['swing_low_price']].dropna()
    no_liq_lows = classify_swing_liquidity(sl, 'low')
    no_liq_lows = no_liq_lows[no_liq_lows['classification'] == 'no_liquidity']

    # timestamps of swings that became BAGs (to distinguish on chart)
    bag_swept_high_ts = {b.swept_ts for b in bull_bags}
    bag_swept_low_ts  = {b.swept_ts for b in bear_bags}

    fig, ax = plt.subplots(figsize=(16, 7), facecolor=BG)
    ax.set_facecolor(BG)

    plot_candles(ax, df)

    # Plot all no-liq swing highs: filled circle if it became a BAG, hollow if not
    first_noliq_h = True
    for ts, row in no_liq_highs.iterrows():
        x = mdates.date2num(ts)
        price = row['swing_high_price']
        is_bag = ts in bag_swept_high_ts
        ax.scatter([x], [price],
                   marker='o', s=45, zorder=6,
                   color=SWEPT_C if is_bag else 'none',
                   edgecolors=SWEPT_C, linewidths=1.2, alpha=0.9,
                   label='No-liq swing high (●=BAG)' if first_noliq_h else '_')
        first_noliq_h = False

    first_noliq_l = True
    for ts, row in no_liq_lows.iterrows():
        x = mdates.date2num(ts)
        price = row['swing_low_price']
        is_bag = ts in bag_swept_low_ts
        ax.scatter([x], [price],
                   marker='o', s=45, zorder=6,
                   color=SWEPT_C if is_bag else 'none',
                   edgecolors=SWEPT_C, linewidths=1.2, alpha=0.9,
                   label='No-liq swing low (●=BAG)' if first_noliq_l else '_')
        first_noliq_l = False

    if bull_bags:
        plot_bags(ax, bull_bags, df, df.index[-1], BAG_B_C, 'bullish', 'Bullish BAG')
    if bear_bags:
        plot_bags(ax, bear_bags, df, df.index[-1], BAG_S_C, 'bearish', 'Bearish BAG')

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
        f'DXY Weekly — Break Away Gaps  ({start} → {end})\n'
        f'Blue zone = Bullish BAG   Red zone = Bearish BAG   '
        f'Orange ● = no-liq swing (filled = BAG formed, hollow = no BAG)',
        color=FG, fontsize=11, pad=10
    )
    ax.legend(facecolor='#161b22', edgecolor='#30363d',
              labelcolor=FG, fontsize=9, loc='upper left')

    out_dir  = os.path.join(os.path.dirname(__file__), 'dxy-weekly-bias')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'dxy-bag-{pd.Timestamp(start).strftime("%Y-%m-%d")}.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f"\nSaved → {out_path}")
    return out_path


if __name__ == '__main__':
    path = main()
    os.system(f'open "{path}"')
