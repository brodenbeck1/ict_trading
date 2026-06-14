"""
High Probability Failure Swing (HPFS)
======================================

Two variants share the same HPFS scan logic but differ in how the LTC is identified:

  RB HPFS (Rejection Block): wick takes liquidity
    bearish LTC: high[i] > high[i-1]  AND  close[i] < high[i-1]
    bullish LTC: low[i]  < low[i-1]   AND  close[i] > low[i-1]

  OB HPFS (Order Block): body (close) takes liquidity
    bearish LTC: close[i] > high[i-1]
    bullish LTC: close[i] < low[i-1]

HPFS scan (same for both): first candle after LTC where extreme is inside the
LTC body — high[j] < open[LTC] (bearish) or low[j] > open[LTC] (bullish).

See knowledge/currency-merchant/price-action/failure-swing.md
"""

from __future__ import annotations

import pandas as pd
from typing import Literal


def find_hpfs(
    df: pd.DataFrame,
    direction: Literal['bearish', 'bullish'],
    ltc_type: Literal['rb', 'ob'] = 'ob',
    scan_forward: int = 6,
) -> pd.DataFrame:
    """
    Detect HPFS levels in a bar series.

    Args:
        df:           OHLCV DataFrame with DatetimeIndex, sorted ascending.
        direction:    'bearish' (HPFS highs) or 'bullish' (HPFS lows).
        ltc_type:     'rb' — rejection block (wick takes);
                      'ob' — order block (body/close takes).
        scan_forward: Max bars after LTC to search for the HPFS candle.

    Returns:
        DataFrame with columns:
          ltc_time   — timestamp of the LTC
          ltc_open   — open of the LTC (body boundary for HPFS scan)
          hpfs_time  — timestamp of the HPFS candle
          hpfs_level — HPFS high (bearish) or low (bullish)
          hpfs_bar   — integer position of HPFS candle in df
          raid_time  — timestamp of first candle to trade through the level (None if active)
          raid_bar   — integer position of raid candle (None if active)
    """
    highs  = df['high'].values
    lows   = df['low'].values
    opens  = df['open'].values
    closes = df['close'].values
    idx    = df.index

    records = []

    for i in range(1, len(df) - 1):
        if direction == 'bearish':
            if ltc_type == 'rb':
                is_ltc = highs[i] > highs[i - 1] and closes[i] < highs[i - 1]
            else:
                is_ltc = closes[i] > highs[i - 1]
        else:
            if ltc_type == 'rb':
                is_ltc = lows[i] < lows[i - 1] and closes[i] > lows[i - 1]
            else:
                is_ltc = closes[i] < lows[i - 1]

        if not is_ltc:
            continue

        ltc_open = opens[i]

        for j in range(i + 1, min(i + 1 + scan_forward, len(df))):
            if direction == 'bearish' and highs[j] < ltc_open:
                records.append({
                    'ltc_time':   idx[i],
                    'ltc_open':   ltc_open,
                    'hpfs_time':  idx[j],
                    'hpfs_level': highs[j],
                    'hpfs_bar':   j,
                })
                break
            elif direction == 'bullish' and lows[j] > ltc_open:
                records.append({
                    'ltc_time':   idx[i],
                    'ltc_open':   ltc_open,
                    'hpfs_time':  idx[j],
                    'hpfs_level': lows[j],
                    'hpfs_bar':   j,
                })
                break

    if not records:
        return pd.DataFrame(columns=[
            'ltc_time', 'ltc_open', 'hpfs_time', 'hpfs_level',
            'hpfs_bar', 'raid_time', 'raid_bar',
        ])

    result = pd.DataFrame(records)

    # Find the raid candle for each HPFS level
    raid_times, raid_bars = [], []
    for _, row in result.iterrows():
        j = int(row['hpfs_bar'])
        raid_bar = None
        raid_time = None
        for k in range(j + 1, len(df)):
            if direction == 'bearish' and highs[k] > row['hpfs_level']:
                raid_bar  = k
                raid_time = idx[k]
                break
            elif direction == 'bullish' and lows[k] < row['hpfs_level']:
                raid_bar  = k
                raid_time = idx[k]
                break
        raid_times.append(raid_time)
        raid_bars.append(raid_bar)

    result['raid_time'] = raid_times
    result['raid_bar']  = raid_bars

    return result
