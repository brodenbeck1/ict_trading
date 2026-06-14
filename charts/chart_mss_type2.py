"""
MSS Type 2 Examples — Close Past Opposing BAG or Dark Pool
===========================================================

Scans DXY weekly data for all instances where price closes through the far edge
of a bearish or bullish BAG / Dark Pool, confirming a market structure shift
without a traditional swing-level break.

Usage:  python charts/chart_mss_type2.py
Output: charts/dxy-weekly-bias/mss-type2-<start>.png
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
from ict.concepts.dark_pool import find_dark_pools, DarkPool

# ── palette ──────────────────────────────────────────────────────────────────
BG      = '#0d1117'
FG      = '#c9d1d9'
BULL_C  = '#3fb950'
BEAR_C  = '#f85149'
BAG_B_C = '#58a6ff'   # blue  — bullish BAG
BAG_S_C = '#f85149'   # red   — bearish BAG
DP_B_C  = '#39d353'   # green — bullish Dark Pool
DP_S_C  = '#e3b341'   # gold  — bearish Dark Pool
MSS2_C  = '#bc8cff'   # purple — MSS Type 2 marker


def fetch_dxy(start: str, end: str, interval: str = '1wk') -> pd.DataFrame:
    raw = yf.download('DX-Y.NYB', start=start, end=end, interval=interval,
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


def first_close_past(df: pd.DataFrame, after_ts: pd.Timestamp,
                     direction: str, edge: float) -> pd.Timestamp | None:
    """First bar after after_ts where close crosses the far edge."""
    future = df[df.index > after_ts]
    if direction == 'bearish':
        hits = future[future['close'] < edge]
    else:
        hits = future[future['close'] > edge]
    return hits.index[0] if len(hits) else None


def plot_zone(ax, bottom: float, top: float, x_start, x_end, color: str, alpha: float = 0.15):
    zone_h = top - bottom
    rect = Rectangle((x_start, bottom), x_end - x_start, zone_h,
                      facecolor=color, edgecolor=color, alpha=alpha, lw=0, zorder=3)
    ax.add_patch(rect)
    ax.hlines([bottom, top], x_start, x_end,
              colors=color, linewidths=0.8, linestyles='solid', alpha=0.5, zorder=4)


def find_mss_type2_events(
    df: pd.DataFrame,
    bags: list[BreakAwayGap],
    dark_pools: list[DarkPool],
    direction: str,
) -> list[dict]:
    """
    Find all first-close-through events that confirm an MSS Type 2.

    The zone direction is always OPPOSITE to the MSS direction:
      bearish MSS → close below bottom of a BULLISH BAG or DP
      bullish MSS → close above top   of a BEARISH BAG or DP
    """
    events = []
    opp = 'bullish' if direction == 'bearish' else 'bearish'

    opp_bags = [b for b in bags if b.fvg.direction == opp]
    opp_dps  = [d for d in dark_pools if d.direction == opp]

    for bag in opp_bags:
        # bearish MSS: close below bullish BAG bottom
        # bullish MSS: close above bearish BAG top
        edge = bag.fvg.bottom if direction == 'bearish' else bag.fvg.top
        break_ts = first_close_past(df, bag.fvg.timestamp, direction, edge)
        if break_ts is not None:
            events.append({
                'break_time':  break_ts,
                'zone_start':  bag.fvg.timestamp,
                'level':       edge,
                'bottom':      bag.fvg.bottom,
                'top':         bag.fvg.top,
                'kind':        'bag',
                'direction':   direction,
                'zone_dir':    opp,
            })

    for dp in opp_dps:
        edge = dp.bottom if direction == 'bearish' else dp.top
        break_ts = first_close_past(df, dp.timestamp, direction, edge)
        if break_ts is not None:
            events.append({
                'break_time':  break_ts,
                'zone_start':  dp.timestamp,
                'level':       edge,
                'bottom':      dp.bottom,
                'top':         dp.top,
                'kind':        'dp',
                'direction':   direction,
                'zone_dir':    opp,
            })

    return sorted(events, key=lambda e: e['break_time'])


def main():
    start, end = '2021-06-01', '2023-06-30'
    df = fetch_dxy(start, end, interval='1wk')
    print(f"Loaded {len(df)} weekly DXY bars ({df.index[0].date()} → {df.index[-1].date()})")

    # ── detect BAGs and Dark Pools ────────────────────────────────────────────
    bear_bags  = find_break_away_gaps(df, 'bearish', swing_lookback=1)
    bull_bags  = find_break_away_gaps(df, 'bullish', swing_lookback=1)
    bear_dps   = find_dark_pools(df, 'bearish', swing_lookback=1)
    bull_dps   = find_dark_pools(df, 'bullish', swing_lookback=1)

    all_bags = bear_bags + bull_bags
    all_dps  = bear_dps + bull_dps

    print(f"BAGs — bearish: {len(bear_bags)}  bullish: {len(bull_bags)}")
    print(f"Dark Pools — bearish: {len(bear_dps)}  bullish: {len(bull_dps)}")

    # ── find all MSS Type 2 events ────────────────────────────────────────────
    bear_events = find_mss_type2_events(df, all_bags, all_dps, 'bearish')
    bull_events = find_mss_type2_events(df, all_bags, all_dps, 'bullish')

    print(f"\nMSS Type 2 — bearish: {len(bear_events)}")
    for e in bear_events:
        print(f"  {e['break_time'].date()}  closed past {e['level']:.2f}  via {e['kind'].upper()}"
              f"  (zone from {e['zone_start'].date()})")

    print(f"\nMSS Type 2 — bullish: {len(bull_events)}")
    for e in bull_events:
        print(f"  {e['break_time'].date()}  closed past {e['level']:.2f}  via {e['kind'].upper()}"
              f"  (zone from {e['zone_start'].date()})")

    # ── plot ──────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(18, 8), facecolor=BG)
    ax.set_facecolor(BG)

    plot_candles(ax, df)
    end_num = mdates.date2num(df.index[-1])

    # Draw BAG zones
    first_bear_bag = True
    for bag in bear_bags:
        x_start = mdates.date2num(bag.fvg.timestamp)
        mit_ts  = first_close_past(df, bag.fvg.timestamp, 'bearish', bag.fvg.bottom)
        x_end   = mdates.date2num(mit_ts) if mit_ts else end_num
        plot_zone(ax, bag.fvg.bottom, bag.fvg.top, x_start, x_end, BAG_S_C)
        ax.hlines(bag.fvg.bottom, x_start, x_end, colors=BAG_S_C, linewidths=1.0,
                  linestyles='solid', zorder=4,
                  label='Bearish BAG' if first_bear_bag else '_')
        first_bear_bag = False

    first_bull_bag = True
    for bag in bull_bags:
        x_start = mdates.date2num(bag.fvg.timestamp)
        mit_ts  = first_close_past(df, bag.fvg.timestamp, 'bullish', bag.fvg.top)
        x_end   = mdates.date2num(mit_ts) if mit_ts else end_num
        plot_zone(ax, bag.fvg.bottom, bag.fvg.top, x_start, x_end, BAG_B_C)
        ax.hlines(bag.fvg.top, x_start, x_end, colors=BAG_B_C, linewidths=1.0,
                  linestyles='solid', zorder=4,
                  label='Bullish BAG' if first_bull_bag else '_')
        first_bull_bag = False

    # Draw Dark Pool zones
    first_bear_dp = True
    for dp in bear_dps:
        x_start = mdates.date2num(dp.timestamp)
        mit_ts  = first_close_past(df, dp.timestamp, 'bearish', dp.bottom)
        x_end   = mdates.date2num(mit_ts) if mit_ts else end_num
        plot_zone(ax, dp.bottom, dp.top, x_start, x_end, DP_S_C, alpha=0.12)
        ax.hlines(dp.bottom, x_start, x_end, colors=DP_S_C, linewidths=0.9,
                  linestyles='dashed', zorder=4,
                  label='Bearish Dark Pool' if first_bear_dp else '_')
        first_bear_dp = False

    first_bull_dp = True
    for dp in bull_dps:
        x_start = mdates.date2num(dp.timestamp)
        mit_ts  = first_close_past(df, dp.timestamp, 'bullish', dp.top)
        x_end   = mdates.date2num(mit_ts) if mit_ts else end_num
        plot_zone(ax, dp.bottom, dp.top, x_start, x_end, DP_B_C, alpha=0.12)
        ax.hlines(dp.top, x_start, x_end, colors=DP_B_C, linewidths=0.9,
                  linestyles='dashed', zorder=4,
                  label='Bullish Dark Pool' if first_bull_dp else '_')
        first_bull_dp = False

    # MSS Type 2 markers — purple diamond at the break bar / level
    first_bear_mss = True
    for e in bear_events:
        xm = mdates.date2num(e['break_time'])
        ax.scatter([xm], [e['level']], marker='D', color=MSS2_C,
                   s=120, zorder=9, edgecolors='white', linewidths=0.5,
                   label='MSS Type 2 (bearish)' if first_bear_mss else '_')
        first_bear_mss = False
        ax.annotate(e['kind'].upper(), xy=(xm, e['level']),
                    xytext=(0, -14), textcoords='offset points',
                    color=MSS2_C, fontsize=7, ha='center', zorder=10)

    first_bull_mss = True
    for e in bull_events:
        xm = mdates.date2num(e['break_time'])
        ax.scatter([xm], [e['level']], marker='D', color=MSS2_C,
                   s=120, zorder=9, edgecolors='white', linewidths=0.5,
                   label='MSS Type 2 (bullish)' if first_bull_mss else '_')
        first_bull_mss = False
        ax.annotate(e['kind'].upper(), xy=(xm, e['level']),
                    xytext=(0, 10), textcoords='offset points',
                    color=MSS2_C, fontsize=7, ha='center', zorder=10)

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
        f'DXY Weekly — MSS Type 2: Close Past Opposing BAG / Dark Pool  ({start} → {end})\n'
        'Purple ◆ = MSS Type 2  |  Solid zone = BAG  |  Dashed zone = Dark Pool',
        color=FG, fontsize=11, pad=10,
    )
    ax.legend(facecolor='#161b22', edgecolor='#30363d',
              labelcolor=FG, fontsize=8, loc='upper left')

    out_dir  = os.path.join(os.path.dirname(__file__), 'dxy-weekly-bias')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'mss-type2-{pd.Timestamp(start).strftime("%Y-%m-%d")}.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f"\nSaved → {out_path}")
    return out_path


if __name__ == '__main__':
    path = main()
    os.system(f'open "{path}"')
