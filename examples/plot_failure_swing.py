"""
Plot High Probability Failure Swing (HPFS) examples — NQ 5m.

HPFS detection (bearish):
  1. Liquidity-taking candle (LTC): high[i] > high[i-1]  (sweeps prior high)
                                    close[i] < high[i-1]  (closes back below = rejection)
  2. Scan forward from LTC: first candle j where high[j] < open[i] = HPFS
     (the first untested high inside the LTC body — stops rest above it)

Mirror logic for bullish HPFS (sweeps prior low, closes above, first low[j] > open[i]).
"""

import os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ict import DataLoader

# ── params ────────────────────────────────────────────────────────────────────
SCAN_FORWARD   = 6    # max bars after LTC to search for the HPFS candle
UNTESTED_BARS  = 20   # bars forward the HPFS level must remain untested
CONTEXT_BEFORE = 15
CONTEXT_AFTER  = 25
N_EXAMPLES     = 6

# ── load data ─────────────────────────────────────────────────────────────────
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))
loader = DataLoader(timeframe='5T', weeks=26, data_dir=data_dir)
df = loader.read_NQ().dropna(subset=['open','high','low','close']).reset_index()

opens  = df['open'].values
highs  = df['high'].values
lows   = df['low'].values
closes = df['close'].values
n      = len(df)

# ── detect HPFS ───────────────────────────────────────────────────────────────
examples = []

for i in range(1, n - SCAN_FORWARD - UNTESTED_BARS - 1):

    # ── BEARISH HPFS ──────────────────────────────────────────────────────
    # LTC: wicks above prior candle's high, closes back below it
    ltc_swept_high = highs[i] > highs[i-1]
    ltc_rejected   = closes[i] < highs[i-1]

    if ltc_swept_high and ltc_rejected:
        ltc_open = opens[i]
        # scan forward for first candle with high < LTC open
        for j in range(i+1, min(i+1+SCAN_FORWARD, n-UNTESTED_BARS-1)):
            if highs[j] < ltc_open:
                # confirm HPFS level untested for UNTESTED_BARS
                hpfs_level = highs[j]
                future = highs[j+1: j+1+UNTESTED_BARS]
                if len(future) > 0 and future.max() < hpfs_level:
                    examples.append({
                        'type'      : 'bearish',
                        'ltc_idx'   : i,
                        'hpfs_idx'  : j,
                        'hpfs_level': hpfs_level,
                        'ltc_open'  : ltc_open,
                        'swept_high': highs[i-1],
                    })
                break   # only take the FIRST qualifying candle after LTC

    # ── BULLISH HPFS ──────────────────────────────────────────────────────
    # LTC: wicks below prior candle's low, closes back above it
    ltc_swept_low  = lows[i] < lows[i-1]
    ltc_rejected   = closes[i] > lows[i-1]

    if ltc_swept_low and ltc_rejected:
        ltc_open = opens[i]
        for j in range(i+1, min(i+1+SCAN_FORWARD, n-UNTESTED_BARS-1)):
            if lows[j] > ltc_open:
                hpfs_level = lows[j]
                future = lows[j+1: j+1+UNTESTED_BARS]
                if len(future) > 0 and future.min() > hpfs_level:
                    examples.append({
                        'type'      : 'bullish',
                        'ltc_idx'   : i,
                        'hpfs_idx'  : j,
                        'hpfs_level': hpfs_level,
                        'ltc_open'  : ltc_open,
                        'swept_low' : lows[i-1],
                    })
                break

print(f"Found {len(examples)} HPFS candidates")

# deduplicate: skip any HPFS within 8 bars of a prior one
filtered, last_idx = [], -20
for ex in sorted(examples, key=lambda x: x['hpfs_idx']):
    if ex['hpfs_idx'] - last_idx > 8:
        filtered.append(ex)
        last_idx = ex['hpfs_idx']

print(f"After dedup: {len(filtered)}")

step = max(1, len(filtered) // N_EXAMPLES)
picks = filtered[::step][:N_EXAMPLES]

# ── plot ──────────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(20, 12), facecolor='#0d1117')
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.48, wspace=0.28)

def draw_candles(ax, chunk):
    for j, row in chunk.iterrows():
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        color = '#3fb950' if c >= o else '#f85149'
        ax.plot([j, j], [l, h], color=color, linewidth=0.9, zorder=2)
        body_bot = min(o, c)
        body_top = max(o, c)
        height   = max(body_top - body_bot, (h - l) * 0.04)
        rect = plt.Rectangle((j - 0.35, body_bot), 0.7, height, color=color, zorder=3)
        ax.add_patch(rect)

for plot_num, ex in enumerate(picks):
    row_idx = plot_num // 3
    col_idx = plot_num  % 3
    ax = fig.add_subplot(gs[row_idx, col_idx])
    ax.set_facecolor('#0d1117')
    for sp in ax.spines.values():
        sp.set_color('#30363d')
    ax.tick_params(colors='#8b949e', labelsize=7)

    ltc  = ex['ltc_idx']
    hpfs = ex['hpfs_idx']

    start = max(0, ltc - CONTEXT_BEFORE)
    end   = min(n, hpfs + CONTEXT_AFTER + 1)
    chunk = df.iloc[start:end].copy().reset_index(drop=True)

    ltc_loc  = ltc  - start
    hpfs_loc = hpfs - start

    draw_candles(ax, chunk)

    # LTC candle — orange highlight
    ax.axvline(ltc_loc, color='#f0883e', linewidth=1.2, alpha=0.5, zorder=1)

    # LTC open line — shows the threshold the HPFS must be below
    ax.axhline(ex['ltc_open'], color='#f0883e', linewidth=0.8,
               linestyle=':', alpha=0.7, zorder=3)

    # swept prior extreme
    swept_key = 'swept_high' if ex['type'] == 'bearish' else 'swept_low'
    ax.axhline(ex[swept_key], color='#8b949e', linewidth=0.7,
               linestyle=':', alpha=0.5, zorder=3)

    # HPFS candle — yellow highlight
    ax.axvline(hpfs_loc, color='#e3b341', linewidth=1.2, alpha=0.5, zorder=1)

    # HPFS level line extending to right
    ax.axhline(ex['hpfs_level'], color='#e3b341', linewidth=1.1,
               linestyle='--', alpha=0.9, zorder=4)

    # annotation
    hpfs_row = chunk.iloc[hpfs_loc]
    rng = hpfs_row['high'] - hpfs_row['low']
    if ex['type'] == 'bearish':
        ax.annotate('HPFS HIGH',
                    xy=(hpfs_loc, ex['hpfs_level']),
                    xytext=(hpfs_loc + 1.5, ex['hpfs_level'] + rng * 1.5),
                    color='#e3b341', fontsize=7, va='bottom',
                    arrowprops=dict(arrowstyle='->', color='#e3b341', lw=0.8))
    else:
        ax.annotate('HPFS LOW',
                    xy=(hpfs_loc, ex['hpfs_level']),
                    xytext=(hpfs_loc + 1.5, ex['hpfs_level'] - rng * 1.5),
                    color='#e3b341', fontsize=7, va='top',
                    arrowprops=dict(arrowstyle='->', color='#e3b341', lw=0.8))

    ax.text(ltc_loc + 0.3,
            ex['ltc_open'],
            'LTC open',
            color='#f0883e', fontsize=6, va='bottom')

    ts = df.iloc[ltc]['timestamp'].strftime('%Y-%m-%d %H:%M')
    bars_apart = hpfs - ltc
    ax.set_title(f"{ex['type'].upper()} HPFS  |  {ts}  |  HPFS {bars_apart}b after LTC",
                 color='#e6edf3', fontsize=8, pad=5)

    xticks = sorted({0, ltc_loc, hpfs_loc, len(chunk)-1})
    ax.set_xticks(xticks)
    ax.set_xticklabels(
        [chunk.iloc[t]['timestamp'].strftime('%H:%M') for t in xticks],
        fontsize=6, color='#8b949e'
    )

fig.suptitle(
    'High Probability Failure Swing (HPFS) Examples — NQ 5m\n'
    'Orange = LTC (sweep + rejection)  |  Yellow = HPFS level (first high/low inside LTC body)',
    color='#e6edf3', fontsize=11, y=0.98
)

out = os.path.join(os.path.dirname(__file__), 'failure_swing_examples.png')
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved → {out}")
plt.show()
