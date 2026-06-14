"""
Find and plot a rejection block example from NQ 5m data.

A rejection block is the wick zone of a long-tailed candle that swept
a prior swing high/low liquidity pool and violently rejected.
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ict import DataLoader

# ── params ────────────────────────────────────────────────────────────────────
WICK_DOMINANCE = 1.5      # wick must be >= 1.5x body
SWING_LOOKBACK = 20       # bars to look back for prior swing extreme
CONTEXT_BARS   = 80       # bars of context to show around the RB candle

# ── load data ─────────────────────────────────────────────────────────────────
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../Data'))
loader = DataLoader(timeframe='5T', weeks=26, data_dir=data_dir)
df = loader.read_NQ()
df = df.dropna(subset=['open', 'high', 'low', 'close'])

# ── detect rejection block candles ────────────────────────────────────────────
opens  = df['open'].values
highs  = df['high'].values
lows   = df['low'].values
closes = df['close'].values

body_size  = np.abs(closes - opens)
upper_wick = highs - np.maximum(opens, closes)
lower_wick = np.minimum(opens, closes) - lows

candidates = []

for i in range(SWING_LOOKBACK, len(df) - 5):
    body = body_size[i]
    if body == 0:
        body = 0.25  # avoid division by zero on doji

    # bearish RB: long upper wick that swept a prior high
    if upper_wick[i] >= WICK_DOMINANCE * body:
        prior_high = highs[i - SWING_LOOKBACK:i].max()
        if highs[i] > prior_high:   # swept buy stops above prior swing high
            # zone: (max(open,close), high)
            zone_lo = max(opens[i], closes[i])
            zone_hi = highs[i]
            candidates.append({
                'idx': i,
                'type': 'bearish',
                'zone_lo': zone_lo,
                'zone_hi': zone_hi,
                'wick_ratio': upper_wick[i] / body,
            })

    # bullish RB: long lower wick that swept a prior low
    if lower_wick[i] >= WICK_DOMINANCE * body:
        prior_low = lows[i - SWING_LOOKBACK:i].min()
        if lows[i] < prior_low:   # swept sell stops below prior swing low
            zone_lo = lows[i]
            zone_hi = min(opens[i], closes[i])
            candidates.append({
                'idx': i,
                'type': 'bullish',
                'zone_lo': zone_lo,
                'zone_hi': zone_hi,
                'wick_ratio': lower_wick[i] / body,
            })

print(f"Found {len(candidates)} rejection block candidates")

# pick the one with the highest wick ratio for a clean example
candidates.sort(key=lambda x: x['wick_ratio'], reverse=True)
rb = candidates[0]
print(f"Best example: {rb['type']} at bar {rb['idx']} "
      f"({df.index[rb['idx']]})  wick/body={rb['wick_ratio']:.1f}x")

# ── slice context window ───────────────────────────────────────────────────────
i = rb['idx']
start = max(0, i - CONTEXT_BARS // 2)
end   = min(len(df), i + CONTEXT_BARS // 2)
chunk = df.iloc[start:end].copy()
chunk = chunk.reset_index()

rb_local = i - start   # RB candle position in chunk

# ── plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(16, 7))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#0d1117')

for spine in ax.spines.values():
    spine.set_color('#30363d')
ax.tick_params(colors='#8b949e')
ax.xaxis.label.set_color('#8b949e')
ax.yaxis.label.set_color('#8b949e')

# draw candles
for j, row in chunk.iterrows():
    x = j
    o, h, l, c = row['open'], row['high'], row['low'], row['close']
    color = '#3fb950' if c >= o else '#f85149'
    ax.plot([x, x], [l, h], color=color, linewidth=0.8, zorder=2)
    body_bot = min(o, c)
    body_top = max(o, c)
    height = max(body_top - body_bot, 0.5)
    rect = plt.Rectangle((x - 0.35, body_bot), 0.7, height,
                          color=color, zorder=3)
    ax.add_patch(rect)

# highlight the RB candle
rb_row = chunk.iloc[rb_local]
ax.axvline(rb_local, color='#e3b341', linewidth=1.2, alpha=0.5, zorder=1)

# shade the rejection block zone
zone_color = '#f85149' if rb['type'] == 'bearish' else '#3fb950'
ax.axhspan(rb['zone_lo'], rb['zone_hi'], alpha=0.18, color=zone_color, zorder=0)
ax.axhline(rb['zone_lo'], color=zone_color, linewidth=0.8, linestyle='--', alpha=0.7)
ax.axhline(rb['zone_hi'], color=zone_color, linewidth=0.8, linestyle='--', alpha=0.7)

# label
direction = "BEARISH" if rb['type'] == 'bearish' else "BULLISH"
zone_mid = (rb['zone_lo'] + rb['zone_hi']) / 2
ax.text(rb_local + 1.5, zone_mid,
        f"{direction} RB\n(wick/body = {rb['wick_ratio']:.1f}×)",
        color=zone_color, fontsize=9, va='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#161b22', edgecolor=zone_color, alpha=0.9))

# x-axis labels: show every ~10 bars
tick_step = max(1, len(chunk) // 8)
ticks = list(range(0, len(chunk), tick_step))
ax.set_xticks(ticks)
ax.set_xticklabels(
    [chunk.iloc[t]['timestamp'].strftime('%m/%d %H:%M') for t in ticks],
    rotation=30, ha='right', fontsize=8, color='#8b949e'
)

ax.set_title(
    f"Rejection Block — NQ 5m  |  {chunk.iloc[rb_local]['timestamp'].strftime('%Y-%m-%d %H:%M')} UTC",
    color='#e6edf3', fontsize=13, pad=10
)
ax.set_ylabel('Price', color='#8b949e')

rb_patch = mpatches.Patch(color=zone_color, alpha=0.5,
                           label=f'{direction} rejection block zone')
ax.legend(handles=[rb_patch], facecolor='#161b22', edgecolor='#30363d',
          labelcolor='#e6edf3', fontsize=9)

plt.tight_layout()
out = os.path.join(os.path.dirname(__file__), 'rejection_block_example.png')
plt.savefig(out, dpi=150, bbox_inches='tight')
print(f"Saved → {out}")
plt.show()
