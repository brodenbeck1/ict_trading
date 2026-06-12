"""
Premium / Discount & Equilibrium
==================================

Within any dealing range the 50% level (EQ) splits price into premium (above)
and discount (below). Never buy premium, never sell discount.

See knowledge/ict/pd-arrays/premium-discount.md
"""

import pandas as pd
from typing import Optional

from ict.registry import concept


@concept("premium-discount")
def premium_discount(
    daily_df: pd.DataFrame,
    dealing_range_days: int = 20,
) -> str:
    """
    Classify current price as premium, discount, or at equilibrium.

    Args:
        daily_df:           Daily OHLCV bars, DatetimeIndex.
        dealing_range_days: Bars defining the governing dealing range.

    Returns:
        'bullish' (price in discount — favors longs) |
        'bearish' (price in premium — favors shorts) |
        'neutral' (at EQ or no valid range)
    """
    result = premium_discount_levels(daily_df, dealing_range_days)
    return result['direction']


def premium_discount_levels(
    daily_df: pd.DataFrame,
    dealing_range_days: int = 20,
) -> dict:
    """
    Return the full premium/discount context: range extremes, EQ, position ratio,
    and direction.

    Returns:
        {direction, range_high, range_low, equilibrium, position, last_close}
        position: 0.0 = range_low, 1.0 = range_high; < 0.5 = discount, > 0.5 = premium
    """
    if daily_df is None or len(daily_df) < 2:
        return {
            'direction': 'neutral', 'range_high': None, 'range_low': None,
            'equilibrium': None, 'position': None, 'last_close': None,
        }

    window     = daily_df.tail(dealing_range_days)
    rng_hi     = float(window['high'].max())
    rng_lo     = float(window['low'].min())
    last_close = float(daily_df['close'].iloc[-1])

    if rng_hi <= rng_lo:
        return {
            'direction': 'neutral', 'range_high': rng_hi, 'range_low': rng_lo,
            'equilibrium': None, 'position': None, 'last_close': last_close,
        }

    eq       = (rng_hi + rng_lo) / 2
    position = (last_close - rng_lo) / (rng_hi - rng_lo)

    if last_close < eq:
        direction = 'bullish'   # discount — favors longs
    elif last_close > eq:
        direction = 'bearish'   # premium — favors shorts
    else:
        direction = 'neutral'   # exactly at EQ

    return {
        'direction':   direction,
        'range_high':  rng_hi,
        'range_low':   rng_lo,
        'equilibrium': eq,
        'position':    position,
        'last_close':  last_close,
    }
