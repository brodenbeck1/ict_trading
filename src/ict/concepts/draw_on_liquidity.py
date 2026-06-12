"""
Draw on Liquidity (DOL)
=======================

The nearest untested swing pool in the bias direction — the level price is
being drawn toward. Bullish when the nearest unswept swing high is closer
than the nearest unswept swing low.

See knowledge/ict/daily-bias/draw-on-liquidity.md
"""

import pandas as pd
from typing import Optional

from ict.registry import concept
from ict.concepts.market_structure import SwingPointScanner


@concept("draw-on-liquidity", depends_on=["swing-points"])
def draw_on_liquidity(
    daily_df: pd.DataFrame,
    dealing_range_days: int = 20,
    swing_lookback: int = 3,
) -> str:
    """
    Determine the draw on liquidity direction from the daily chart.

    Compares the distance from current price to the nearest untested swing
    high above vs. the nearest untested swing low below. The closer pool is
    the active draw.

    Args:
        daily_df:           Daily OHLCV bars, DatetimeIndex.
        dealing_range_days: Lookback window for swing detection.
        swing_lookback:     Bar lookback passed to SwingPointScanner.

    Returns:
        'bullish' (draw is above, price targeting highs) |
        'bearish' (draw is below, price targeting lows) |
        'neutral' (no swings found)
    """
    result = draw_on_liquidity_levels(daily_df, dealing_range_days, swing_lookback)
    return result['direction']


def draw_on_liquidity_levels(
    daily_df: pd.DataFrame,
    dealing_range_days: int = 20,
    swing_lookback: int = 3,
) -> dict:
    """
    Return the full DOL context: nearest swing levels above and below, and direction.

    Returns:
        {direction, nearest_high, nearest_low, last_close}
    """
    if daily_df is None or len(daily_df) < 2:
        return {'direction': 'neutral', 'nearest_high': None, 'nearest_low': None, 'last_close': None}

    window     = daily_df.tail(dealing_range_days)
    scanner    = SwingPointScanner(window, lookback=swing_lookback)
    scanner.identify_swings()
    last_close = float(daily_df['close'].iloc[-1])

    highs = (scanner.swing_highs['swing_high_price'].dropna()
             if scanner.swing_highs is not None else pd.Series(dtype=float))
    lows  = (scanner.swing_lows['swing_low_price'].dropna()
             if scanner.swing_lows is not None else pd.Series(dtype=float))

    highs_above  = highs[highs > last_close]
    lows_below   = lows[lows < last_close]
    nearest_high = float(highs_above.min()) if len(highs_above) else None
    nearest_low  = float(lows_below.max())  if len(lows_below)  else None

    if nearest_high is not None and nearest_low is not None:
        direction = 'bullish' if (nearest_high - last_close) <= (last_close - nearest_low) else 'bearish'
    elif nearest_high is not None:
        direction = 'bullish'
    elif nearest_low is not None:
        direction = 'bearish'
    else:
        direction = 'neutral'

    return {
        'direction':    direction,
        'nearest_high': nearest_high,
        'nearest_low':  nearest_low,
        'last_close':   last_close,
    }
