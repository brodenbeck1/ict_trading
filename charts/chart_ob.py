"""
Order Block Chart — body liquidity sweep + validation candle.

Detection:
  Bullish OB: bearish candle whose body CLOSE goes below the most recent swing low;
              validated when a subsequent candle closes ABOVE the OB candle open.
  Bearish OB: bullish candle whose body CLOSE goes above the most recent swing high;
              validated when a subsequent candle closes BELOW the OB candle open.

Only the MOST RECENT unmitigated OB in each direction is shown per display window.
Uses DXY 1h data (Data/dxy_1h.csv).

Usage: python charts/chart_ob.py
Output: charts/ob/ob-DXY-1h.png
"""

import os
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

# ── palette ──────────────────────────────────────────────────────────────────
BG      = '#0d1117'
FG      = '#c9d1d9'
BULL_C  = '#26a641'
BEAR_C  = '#f85149'
BULL_OB = '#58a6ff'   # blue   — bullish OB zone
BEAR_OB = '#f0883e'   # orange — bearish OB zone
VALID_C = '#e3b341'   # gold   — validation candle marker
SWEEP_C = '#bc8cff'   # purple — swept swing level


def load_fixture(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=['timestamp'])
    df = df.rename(columns={'timestamp': 'time'})
    df = df.set_index('time').sort_index()
    df.index = pd.to_datetime(df.index, utc=True)
    return df[['open', 'high', 'low', 'close']].astype(float)


def find_swings(df: pd.DataFrame, lookback: int = 5):
    """Return sorted lists of (bar_index, price) for swing highs and lows."""
    highs, lows = [], []
    for i in range(lookback, len(df) - lookback):
        window = df.iloc[i - lookback: i + lookback + 1]
        if df.iloc[i]['high'] == window['high'].max():
            highs.append((i, df.iloc[i]['high']))
        if df.iloc[i]['low'] == window['low'].min():
            lows.append((i, df.iloc[i]['low']))
    return highs, lows


def detect_obs(df: pd.DataFrame, swing_lookback: int = 5, max_swing_age: int = 15,
               min_body_pct: float = 0.002):
    """
    Returns list of validated OB dicts, one per distinct sweep level (deduped).

    Dedup: if multiple consecutive bearish candles all breach the same swing low,
    keep only the LAST one (the candle immediately before the reversal).

    min_body_pct: minimum body size as fraction of price (filters doji noise).
    """
    highs_list, lows_list = find_swings(df, swing_lookback)

    obs = []

    for i in range(1, len(df)):
        row = df.iloc[i]
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        body = abs(c - o)
        if body / o < min_body_pct:
            continue

        # ── Bullish OB: bearish candle body closes below most recent swing low ──
        if c < o:
            prior_lows = [(j, p) for j, p in lows_list if j < i and (i - j) <= max_swing_age]
            if prior_lows:
                j_low, swing_low = max(prior_lows, key=lambda x: x[0])
                if c < swing_low:
                    # skip if the NEXT candle is also bearish and also breaches the same level
                    # (keep only the last candle of a consecutive sweep run)
                    if i + 1 < len(df):
                        nxt = df.iloc[i + 1]
                        if nxt['close'] < nxt['open'] and nxt['close'] < swing_low:
                            continue
                    valid_idx = None
                    for k in range(i + 1, min(i + 15, len(df))):
                        if df.iloc[k]['close'] > o:
                            valid_idx = k
                            break
                    if valid_idx is not None:
                        obs.append({
                            'direction':   'bullish',
                            'ob_idx':      i,
                            'ob_open':     o,
                            'ob_close':    c,
                            'zone_top':    o,
                            'zone_bot':    c,
                            'sweep_level': swing_low,
                            'valid_idx':   valid_idx,
                        })

        # ── Bearish OB: bullish candle body closes above most recent swing high ──
        elif c > o:
            prior_highs = [(j, p) for j, p in highs_list if j < i and (i - j) <= max_swing_age]
            if prior_highs:
                j_high, swing_high = max(prior_highs, key=lambda x: x[0])
                if c > swing_high:
                    if i + 1 < len(df):
                        nxt = df.iloc[i + 1]
                        if nxt['close'] > nxt['open'] and nxt['close'] > swing_high:
                            continue
                    valid_idx = None
                    for k in range(i + 1, min(i + 15, len(df))):
                        if df.iloc[k]['close'] < o:
                            valid_idx = k
                            break
                    if valid_idx is not None:
                        obs.append({
                            'direction':   'bearish',
                            'ob_idx':      i,
                            'ob_open':     o,
                            'ob_close':    c,
                            'zone_top':    c,
                            'zone_bot':    o,
                            'sweep_level': swing_high,
                            'valid_idx':   valid_idx,
                        })

    return obs


def plot_candles(ax, df, bar_w: float = 0.025):
    for ts, row in df.iterrows():
        x = mdates.date2num(ts)
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        color = BULL_C if c >= o else BEAR_C
        ax.plot([x, x], [l, h], color=color, lw=0.8, zorder=1)
        body_h = abs(c - o) or 0.0005
        rect = Rectangle((x - bar_w, min(o, c)), 2 * bar_w, body_h,
                          facecolor=color, edgecolor=color, lw=0, zorder=2)
        ax.add_patch(rect)


def plot_ob_zone(ax, ob, df, bar_w, first_bull, first_bear):
    color   = BULL_OB if ob['direction'] == 'bullish' else BEAR_OB
    ts_ob   = df.index[ob['ob_idx']]
    ts_end  = df.index[-1]
    x_ob    = mdates.date2num(ts_ob)
    x_end   = mdates.date2num(ts_end)
    mid     = (ob['zone_top'] + ob['zone_bot']) / 2
    zone_h  = ob['zone_top'] - ob['zone_bot']

    # filled rectangle from OB candle to right edge
    lbl = ('Bullish OB' if ob['direction'] == 'bullish' else 'Bearish OB') + ' (validated)'
    show_label = (ob['direction'] == 'bullish' and first_bull) or \
                 (ob['direction'] == 'bearish' and first_bear)
    rect = Rectangle((x_ob - bar_w, ob['zone_bot']), x_end - x_ob + bar_w, zone_h,
                      facecolor=color, alpha=0.15, lw=0, zorder=0,
                      label=lbl if show_label else '_')
    ax.add_patch(rect)

    # proximal / distal edge lines
    ax.hlines([ob['zone_top'], ob['zone_bot']], x_ob, x_end,
              colors=color, linewidths=1.1, linestyles='solid', zorder=4)
    # midpoint
    ax.hlines(mid, x_ob, x_end, colors=color, linewidths=0.5,
              linestyles='dashed', alpha=0.5, zorder=3)

    # circle at OB candle
    anchor = ob['zone_top'] if ob['direction'] == 'bullish' else ob['zone_bot']
    ax.scatter([x_ob], [anchor], marker='o', color=color, s=55, zorder=7)

    # X at swept swing level
    ax.scatter([x_ob], [ob['sweep_level']], marker='x', color=SWEEP_C,
               s=90, linewidths=1.8, zorder=8,
               label='Swept swing level' if show_label else '_')

    # diamond at validation candle
    ts_valid  = df.index[ob['valid_idx']]
    x_valid   = mdates.date2num(ts_valid)
    val_close = df.iloc[ob['valid_idx']]['close']
    ax.scatter([x_valid], [val_close], marker='D', color=VALID_C, s=65, zorder=9,
               label='Validation candle' if show_label else '_')


def main():
    fixture = os.path.join(os.path.dirname(__file__), '..', 'Data', 'dxy_1h.csv')
    df_full = load_fixture(fixture)

    # show a 4-week window so individual OBs are legible
    window_start = df_full.index[0]
    window_end   = window_start + pd.Timedelta(weeks=4)
    df = df_full[window_start:window_end].copy()

    print(f"Loaded {len(df)} 1h bars  ({df.index[0].date()} → {df.index[-1].date()})")

    obs = detect_obs(df, swing_lookback=3, max_swing_age=20, min_body_pct=0.001)
    print(f"Validated OBs: {len(obs)}")
    for ob in obs:
        ts_ob    = df.index[ob['ob_idx']]
        ts_valid = df.index[ob['valid_idx']]
        print(f"  {ob['direction']:8s} OB @ {ts_ob}  "
              f"zone [{ob['zone_bot']:.3f} – {ob['zone_top']:.3f}]  "
              f"sweep={ob['sweep_level']:.3f}  validated @ {ts_valid}")

    # ── plot ─────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(20, 7), facecolor=BG)
    ax.set_facecolor(BG)

    bar_w = (mdates.date2num(df.index[1]) - mdates.date2num(df.index[0])) * 0.4

    plot_candles(ax, df, bar_w)

    first_bull = first_bear = True
    for ob in obs:
        plot_ob_zone(ax, ob, df, bar_w, first_bull, first_bear)
        if ob['direction'] == 'bullish':
            first_bull = False
        else:
            first_bear = False

    # ── cosmetics ─────────────────────────────────────────────────────────────
    for spine in ax.spines.values():
        spine.set_color('#30363d')
    ax.tick_params(colors=FG, labelsize=7)
    ax.yaxis.tick_right()
    ax.set_ylabel('Price', color=FG, labelpad=8)
    ax.yaxis.set_label_position('right')
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.DayLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    plt.xticks(rotation=30, ha='right')
    ax.grid(axis='y', color='#21262d', linewidth=0.4)
    ax.set_title(
        f'Order Block — body liquidity sweep + validation  (DXY 1h  '
        f'{df.index[0].date()} → {df.index[-1].date()})',
        color=FG, fontsize=12, pad=10
    )
    ax.legend(facecolor='#161b22', edgecolor='#30363d',
              labelcolor=FG, fontsize=8, loc='upper left')

    # ── save ──────────────────────────────────────────────────────────────────
    out_dir = os.path.join(os.path.dirname(__file__), 'ob')
    os.makedirs(out_dir, exist_ok=True)
    start_str = df.index[0].strftime('%Y-%m-%d')
    out_path  = os.path.join(out_dir, f'ob-DXY-1h-{start_str}.png')
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches='tight', facecolor=BG)
    plt.close()
    print(f"\nSaved → {out_path}")
    return out_path


if __name__ == '__main__':
    main()
