"""
Daily Bias (Intermediate Model)
================================

Three-signal gate: order flow + draw-on-liquidity + premium/discount must all
agree. Orchestrates three concept detectors; returns the combined verdict.

Lives in models/intermediate/ because it composes multiple concepts rather than
implementing a single primitive — it is itself a building block for full models.

See knowledge/ict/daily-bias/daily-bias.md
"""

import pandas as pd

from ict.registry import concept
from ict.concepts.draw_on_liquidity import draw_on_liquidity
from ict.concepts.premium_discount import premium_discount
from ict.concepts.ohlc_profiles import ohlc_candle_profile  # noqa: F401


@concept("daily-bias")
def daily_bias(
    daily_df: pd.DataFrame,
    lookback: int = 20,
    dealing_range_days: int = 20,
    swing_lookback: int = 3,
) -> str:
    """
    Compute ICT daily bias from the daily chart.

    All three signals must agree; otherwise returns 'neutral'.

    Args:
        daily_df:           Daily OHLCV bars, DatetimeIndex.
        lookback:           Bars for order-flow scoring.
        dealing_range_days: Bars for the dealing range (draw + premium/discount).
        swing_lookback:     Bar lookback for swing detection inside draw-on-liquidity.

    Returns:
        'bullish' | 'bearish' | 'neutral'
    """
    components = daily_bias_components(daily_df, lookback, dealing_range_days, swing_lookback)
    return components['bias']


def daily_bias_components(
    daily_df: pd.DataFrame,
    lookback: int = 20,
    dealing_range_days: int = 20,
    swing_lookback: int = 3,
) -> dict:
    """
    Return each sub-signal plus the combined bias verdict.

    Returns:
        {'order_flow': str, 'draw': str, 'premium_discount': str, 'bias': str}
    """
    neutral = {'order_flow': 'neutral', 'draw': 'neutral', 'premium_discount': 'neutral', 'bias': 'neutral'}
    if daily_df is None or len(daily_df) < max(lookback, 3):
        return neutral

    order_flow = _order_flow(daily_df, lookback)
    draw       = draw_on_liquidity(daily_df, dealing_range_days, swing_lookback)
    prem_disc  = premium_discount(daily_df, dealing_range_days)

    if order_flow == draw == prem_disc == 'bullish':
        bias = 'bullish'
    elif order_flow == draw == prem_disc == 'bearish':
        bias = 'bearish'
    else:
        bias = 'neutral'

    return {'order_flow': order_flow, 'draw': draw, 'premium_discount': prem_disc, 'bias': bias}


# ---------------------------------------------------------------------------
# Order flow sub-signal (no standalone concept slug in the KB)
# ---------------------------------------------------------------------------

def _order_flow(daily_df: pd.DataFrame, n: int) -> str:
    recent = daily_df.tail(n).dropna(subset=['open', 'close'])
    if len(recent) < 2:
        return 'neutral'
    net  = recent['close'].iloc[-1] - recent['close'].iloc[0]
    up   = int((recent['close'] > recent['open']).sum())
    down = int((recent['close'] < recent['open']).sum())
    if net > 0 and up >= down:
        return 'bullish'
    if net < 0 and down >= up:
        return 'bearish'
    return 'neutral'
