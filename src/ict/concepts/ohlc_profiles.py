"""
OHLC / OLHC Candle Profiles
============================

The expected internal delivery sequence of a daily candle given the bias:
  Bearish day = O-H-L-C  (manipulation high, then expansion to low)
  Bullish day = O-L-H-C  (manipulation low, then expansion to high)

See knowledge/ict/daily-bias/ohlc-candle-profiles.md
"""

import pandas as pd

from ict.registry import concept


@concept("ohlc-candle-profiles")
def ohlc_candle_profile(daily_df: pd.DataFrame) -> str:
    """
    Determine the expected intraday delivery profile from recent daily structure.

    Looks at the last 5 daily bars: if highs have been consistently taken without
    lows, expect a bearish O-H-L-C day; if lows taken without highs, expect bullish
    O-L-H-C.

    Args:
        daily_df: Daily OHLCV bars, DatetimeIndex.

    Returns:
        'bearish' | 'bullish' | 'neutral'
    """
    if daily_df is None or len(daily_df) < 2:
        return 'neutral'

    recent     = daily_df.tail(5)
    took_highs = int((recent['high'].diff() > 0).sum())
    took_lows  = int((recent['low'].diff() < 0).sum())

    if took_highs > 0 and took_lows == 0:
        return 'bearish'
    if took_lows > 0 and took_highs == 0:
        return 'bullish'
    return 'neutral'


def entry_side_valid(
    profile: str,
    entry_price: float,
    daily_open: float,
) -> bool:
    """
    Entry-side filter: longs should be below the daily open (buying the manipulation
    low); shorts should be above (selling the manipulation high).

    Args:
        profile:     'bullish' or 'bearish' from ohlc_candle_profile().
        entry_price: Proposed entry price.
        daily_open:  The midnight NY open of the day (true day open).

    Returns:
        True if entry is on the correct side of the open for the profile.
    """
    if profile == 'bullish':
        return entry_price < daily_open
    if profile == 'bearish':
        return entry_price > daily_open
    return False
