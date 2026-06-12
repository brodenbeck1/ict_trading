"""
Fair Value Gap (FVG) Detection
===============================

A Fair Value Gap is a 3-candle imbalance where price moved so quickly that
no overlapping delivery occurred between the prior and subsequent candle.

Bearish FVG (displacement candle is candle[i], moving down):
  - Condition: candle[i-1].low > candle[i+1].high
  - Zone: candle[i+1].high (bottom) to candle[i-1].low (top)
  - Entry limit short: candle[i-1].low (top of gap)

Bullish FVG (displacement candle is candle[i], moving up):
  - Condition: candle[i+1].low > candle[i-1].high
  - Zone: candle[i-1].high (bottom) to candle[i+1].low (top)
  - Entry limit long: candle[i-1].high (bottom of gap)
"""

import pandas as pd
from dataclasses import dataclass

from ict.registry import concept


@dataclass
class FVG:
    timestamp: pd.Timestamp   # timestamp of displacement candle
    direction: str            # 'bearish' or 'bullish'
    top: float                # top of FVG zone
    bottom: float             # bottom of FVG zone
    entry: float              # limit entry price


@concept("fair-value-gap")
def find_fvgs(df: pd.DataFrame, direction: str = 'bearish') -> list:
    """
    Scan df for Fair Value Gaps. Returns list of FVG objects in chronological order.

    Args:
        df: OHLCV DataFrame with DatetimeIndex
        direction: 'bearish' or 'bullish'
    """
    fvgs = []
    for i in range(1, len(df) - 1):
        prev_low = df['low'].iloc[i - 1]
        next_high = df['high'].iloc[i + 1]
        prev_high = df['high'].iloc[i - 1]
        next_low = df['low'].iloc[i + 1]

        if direction == 'bearish' and prev_low > next_high:
            fvgs.append(FVG(
                timestamp=df.index[i],
                direction='bearish',
                top=prev_low,
                bottom=next_high,
                entry=prev_low,
            ))
        elif direction == 'bullish' and next_low > prev_high:
            fvgs.append(FVG(
                timestamp=df.index[i],
                direction='bullish',
                top=next_low,
                bottom=prev_high,
                entry=prev_high,
            ))
    return fvgs
