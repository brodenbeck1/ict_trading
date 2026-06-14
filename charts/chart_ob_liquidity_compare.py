"""
Order Block — Liquidity Source Comparison Chart

Three panels, same 2-week DXY 1h window. Each panel shows:
  - The liquidity levels used as sweep targets (buy-side in blue, sell-side in green)
  - OBs that formed by sweeping those levels (orange=bearish, blue=bullish)

  Row 1 — Pivot swing H/L  (most permissive, every structural high/low)
  Row 2 — HPFS (OB-type)   (failure swings formed after a body LTC)
  Row 3 — REH / REL        (clustered double-stacked equal highs/lows)

Usage: python charts/chart_ob_liquidity_compare.py
Output: charts/ob/ob-liquidity-compare-DXY-1h-<date>.png
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ict.concepts.order_block import find_order_blocks, OrderBlock
from ict.concepts.hpfs import find_hpfs
from ict.concepts.market_structure import SwingPointScanner

# ── palette ───────────────────────────────────────────────────────────────────
BG       = '#0d1117'
FG       = '#c9d1d9'
BULL_C   = '#26a641'
BEAR_C   = '#f85149'
BULL_OB  = '#58a6ff'    # blue   — bullish OB zone
BEAR_OB  = '#f0883e'    # orange — bearish OB zone
BUY_LIQ  = '#58a6ff'    # blue   — buy-side liquidity (highs)
SELL_LIQ = '#3fb950'    # green  — sell-side liquidity (lows)
VALID_C  = '#e3b341'    # gold   — validation candle
SWEEP_C  = '#bc8cff'    # purple — swept level X

SOURCES = [
    ('pivot',   'Pivot Swing H/L  — every structural high/low'),
    ('hpfs_ob', 'HPFS (OB-type LTC)  — body takes prior bar, then fails'),
    ('rel',     'REH / REL  — clustered equal highs/lows'),
]


def load_fixture(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=['timestamp'])
    df = df.rename(columns={'timestamp': 'time'}).set_index('time').sort_index()
    df.index = pd.to_datetime(df.index, utc=True)
    return df[['open', 'high', 'low', 'close']].astype(float)


# ── Liquidity level extractors ────────────────────────────────────────────────

def get_pivot_levels(df: pd.DataFrame, lookback: int = 3
                     ) -> tuple[list[tuple], list[tuple]]:
    """Returns (buy_side [(ts, price)], sell_side [(ts, price)])."""
    buy, sell = [], []
    n = len(df)
    for i in range(lookback, n - lookback):
        hi = df['high'].iloc[i]
        lo = df['low'].iloc[i]
        if hi == df['high'].iloc[i - lookback: i + lookback + 1].max():
            buy.append((df.index[i], float(hi)))
        if lo == df['low'].iloc[i - lookback: i + lookback + 1].min():
            sell.append((df.index[i], float(lo)))
    return buy, sell


def get_hpfs_levels(df: pd.DataFrame, ltc_type: str
                    ) -> tuple[list[tuple], list[tuple]]:
    """Returns (buy_side [(ts, price)], sell_side [(ts, price)])."""
    bear = find_hpfs(df, 'bearish', ltc_type=ltc_type)  # highs  = buy-side
    bull = find_hpfs(df, 'bullish', ltc_type=ltc_type)  # lows   = sell-side
    buy  = [(r['hpfs_time'], float(r['hpfs_level'])) for _, r in bear.iterrows()]
    sell = [(r['hpfs_time'], float(r['hpfs_level'])) for _, r in bull.iterrows()]
    return buy, sell


def get_rel_levels(df: pd.DataFrame, lookback: int = 3
                   ) -> tuple[list[tuple], list[tuple]]:
    """Returns (buy_side [(ts, price)], sell_side [(ts, price)])."""
    scanner = SwingPointScanner(df, lookback=lookback)
    scanner.identify_swings()
    buy  = [(c['timestamps'][0], float(c['price']))
            for c in scanner.find_relative_equal_highs()]
    sell = [(c['timestamps'][0], float(c['price']))
            for c in scanner.find_relative_equal_lows()]
    return buy, sell


def levels_for_source(df, source, lookback=3):
    if source == 'pivot':
        return get_pivot_levels(df, lookback)
    elif source == 'hpfs_ob':
        return get_hpfs_levels(df, ltc_type='ob')
    elif source == 'rel':
        return get_rel_levels(df, lookback)
    return [], []


# ── Plotting helpers ──────────────────────────────────────────────────────────

def plot_candles(ax, df, bar_w):
    for ts, row in df.iterrows():
        x = mdates.date2num(ts)
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        color = BULL_C if c >= o else BEAR_C
        ax.plot([x, x], [l, h], color=color, lw=0.7, zorder=1)
        bh = abs(c - o) or 0.0005
        rect = Rectangle((x - bar_w, min(o, c)), 2 * bar_w, bh,
                          facecolor=color, edgecolor=color, lw=0, zorder=2)
        ax.add_patch(rect)


def plot_liquidity_levels(ax, buy_levels, sell_levels, df):
    """Draw each liquidity level from its formation bar to where it's first taken."""
    x_end = mdates.date2num(df.index[-1])

    def first_taken(ts, price, side):
        future = df[df.index > ts]
        col = 'high' if side == 'buy' else 'low'
        hit = future[future[col] > price] if side == 'buy' else future[future[col] < price]
        return hit.index[0] if len(hit) else None

    # buy-side highs (blue dotted)
    first_buy = True
    for ts, price in buy_levels:
        x_start = mdates.date2num(ts)
        taken = first_taken(ts, price, 'buy')
        x_stop = mdates.date2num(taken) if taken is not None else x_end
        ax.hlines(price, x_start, x_stop, colors=BUY_LIQ, linewidths=0.8,
                  linestyles='dotted', alpha=0.6, zorder=3,
                  label='Buy-side pool (high)' if first_buy else '_')
        if taken is not None and x_stop < x_end:
            ax.hlines(price, x_stop, x_end, colors=BUY_LIQ, linewidths=0.4,
                      linestyles='dotted', alpha=0.2, zorder=2)
        first_buy = False

    # sell-side lows (green dotted)
    first_sell = True
    for ts, price in sell_levels:
        x_start = mdates.date2num(ts)
        taken = first_taken(ts, price, 'sell')
        x_stop = mdates.date2num(taken) if taken is not None else x_end
        ax.hlines(price, x_start, x_stop, colors=SELL_LIQ, linewidths=0.8,
                  linestyles='dotted', alpha=0.6, zorder=3,
                  label='Sell-side pool (low)' if first_sell else '_')
        if taken is not None and x_stop < x_end:
            ax.hlines(price, x_stop, x_end, colors=SELL_LIQ, linewidths=0.4,
                      linestyles='dotted', alpha=0.2, zorder=2)
        first_sell = False


def plot_obs(ax, obs: list[OrderBlock], df: pd.DataFrame, bar_w: float):
    first_bull = first_bear = True
    for ob in obs:
        color  = BULL_OB if ob.direction == 'bullish' else BEAR_OB
        x_ob   = mdates.date2num(ob.timestamp)
        x_end  = mdates.date2num(df.index[-1])
        zone_h = ob.zone_top - ob.zone_bot

        show = (ob.direction == 'bullish' and first_bull) or \
               (ob.direction == 'bearish' and first_bear)
        lbl = ('Bullish OB' if ob.direction == 'bullish' else 'Bearish OB') + ' (validated)'

        rect = Rectangle((x_ob - bar_w, ob.zone_bot), x_end - x_ob + bar_w, zone_h,
                          facecolor=color, alpha=0.22, lw=0, zorder=5,
                          label=lbl if show else '_')
        ax.add_patch(rect)
        ax.hlines([ob.zone_top, ob.zone_bot], x_ob, x_end,
                  colors=color, linewidths=1.2, linestyles='solid', zorder=6)
        ax.hlines(ob.midpoint, x_ob, x_end, colors=color, linewidths=0.5,
                  linestyles='dashed', alpha=0.5, zorder=5)

        # OB candle marker
        anchor = ob.zone_top if ob.direction == 'bullish' else ob.zone_bot
        ax.scatter([x_ob], [anchor], marker='o', color=color, s=45, zorder=8)

        # swept level X (purple)
        ax.scatter([x_ob], [ob.sweep_level], marker='x', color=SWEEP_C,
                   s=80, linewidths=1.8, zorder=9,
                   label='Swept level' if show else '_')

        # validation diamond (gold)
        if ob.validation_time is not None and ob.validation_time in df.index:
            x_v = mdates.date2num(ob.validation_time)
            v_c = float(df.loc[ob.validation_time, 'close'])
            ax.scatter([x_v], [v_c], marker='D', color=VALID_C, s=55, zorder=10,
                       label='Validation' if show else '_')

        if ob.direction == 'bullish':
            first_bull = False
        else:
            first_bear = False


def style_ax(ax, title):
    for spine in ax.spines.values():
        spine.set_color('#30363d')
    ax.set_facecolor(BG)
    ax.tick_params(colors=FG, labelsize=7)
    ax.yaxis.tick_right()
    ax.yaxis.set_label_position('right')
    ax.set_ylabel('Price', color=FG, labelpad=6, fontsize=8)
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', color='#21262d', linewidth=0.4)
    ax.set_title(title, color=FG, fontsize=9, loc='left', pad=5)
    ax.legend(facecolor='#161b22', edgecolor='#30363d',
              labelcolor=FG, fontsize=7, loc='upper left', framealpha=0.85,
              ncol=2)


def main():
    fixture = os.path.join(os.path.dirname(__file__), '..', 'Data', 'dxy_1h.csv')
    df_full = load_fixture(fixture)

    # 2-week window
    window_end = df_full.index[0] + pd.Timedelta(weeks=2)
    df = df_full[df_full.index <= window_end].copy()

    print(f"Window: {df.index[0].date()} → {df.index[-1].date()}  ({len(df)} bars)")

    bar_w = (mdates.date2num(df.index[1]) - mdates.date2num(df.index[0])) * 0.4

    fig, axes = plt.subplots(len(SOURCES), 1, figsize=(22, 5 * len(SOURCES)),
                              facecolor=BG, sharex=True)
    fig.subplots_adjust(hspace=0.06)

    for ax, (source, label) in zip(axes, SOURCES):
        obs = find_order_blocks(df, direction='both', liquidity_source=source,
                                swing_lookback=3, max_swing_age=20, min_body_pct=0.001)
        buy_levels, sell_levels = levels_for_source(df, source)

        n_bull = sum(1 for ob in obs if ob.direction == 'bullish')
        n_bear = sum(1 for ob in obs if ob.direction == 'bearish')
        n_buy  = len(buy_levels)
        n_sell = len(sell_levels)
        title = (f'{label}   |   '
                 f'{n_buy} buy-side pools  ·  {n_sell} sell-side pools   →   '
                 f'{len(obs)} OBs  ({n_bull}↑  {n_bear}↓)')

        plot_candles(ax, df, bar_w)
        plot_liquidity_levels(ax, buy_levels, sell_levels, df)
        plot_obs(ax, obs, df, bar_w)
        style_ax(ax, title)

        print(f"\n[{source}]  buy={n_buy}  sell={n_sell}  obs={len(obs)}")
        for ob in obs:
            print(f"  {ob.direction:8s}  {ob.timestamp.strftime('%m-%d %H:%M')}  "
                  f"zone=[{ob.zone_bot:.3f}–{ob.zone_top:.3f}]  sweep={ob.sweep_level:.3f}")

    fig.suptitle(
        f'Order Block — Liquidity Source Comparison  '
        f'(DXY 1h  {df.index[0].date()} → {df.index[-1].date()})',
        color=FG, fontsize=12, y=1.002
    )

    out_dir   = os.path.join(os.path.dirname(__file__), 'ob')
    os.makedirs(out_dir, exist_ok=True)
    start_str = df.index[0].strftime('%Y-%m-%d')
    out_path  = os.path.join(out_dir, f'ob-liquidity-compare-DXY-1h-{start_str}.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f'\nSaved → {out_path}')
    return out_path


if __name__ == '__main__':
    path = main()
    os.system(f'open "{path}"')
