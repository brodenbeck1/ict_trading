"""
Pool Validity — swing liquidity classification and HPFS-based DOL filter
========================================================================

classify_swing_liquidity()
    Tags each swing high/low as 'failure_swing' (untouched liquidity) or
    'no_liquidity' (already swept the prior swing). Implements the
    swing-without-liquidity concept.
    See knowledge/currency-merchant/price-action/swing-without-liquidity.md

hpfs_pools()
    Wraps find_hpfs() to identify valid DOL candidates, optionally filtered
    to the correct side of the weekly open.
    See knowledge/currency-merchant/price-action/failure-swing.md
"""

import pandas as pd
from typing import Literal, Optional

from ict.registry import concept
from ict.concepts.hpfs import find_hpfs


@concept("swing-without-liquidity")
def classify_swing_liquidity(
    swing_points: pd.DataFrame,
    swing_type: Literal['high', 'low'],
) -> pd.DataFrame:
    """
    Classify each swing high or low as 'failure_swing' or 'no_liquidity'.

    failure_swing : extreme did NOT take the prior swing extreme — untouched
                    liquidity still rests above (high) or below (low).
    no_liquidity  : extreme already swept the prior swing extreme — those
                    stops have been distributed; no meaningful orders remain.

    Equal prices are NOT disqualified — relative equal highs/lows represent
    doubled-up liquidity, not consumed liquidity.

    Args:
        swing_points: DataFrame from SwingPointScanner (.swing_highs or
                      .swing_lows) — must contain 'swing_high_price' or
                      'swing_low_price' column.
        swing_type:   'high' or 'low'.

    Returns:
        Input DataFrame with an added 'classification' column.
    """
    price_col = 'swing_high_price' if swing_type == 'high' else 'swing_low_price'
    result = swing_points[[price_col]].copy()

    labels = []
    prev = None
    for price in result[price_col]:
        if prev is None:
            labels.append('failure_swing')
        elif swing_type == 'high':
            labels.append('no_liquidity' if price > prev else 'failure_swing')
        else:
            labels.append('no_liquidity' if price < prev else 'failure_swing')
        prev = price

    result['classification'] = labels
    return result


def hpfs_pools(
    df: pd.DataFrame,
    direction: Literal['bullish', 'bearish'],
    ltc_type: Literal['rb', 'ob'] = 'ob',
    weekly_open: float | None = None,
) -> pd.DataFrame:
    """
    Return HPFS levels that qualify as DOL candidates, optionally filtered
    to the correct side of the weekly open.

    For a bullish week only pools ABOVE weekly_open are candidates.
    For a bearish week only pools BELOW weekly_open are candidates.

    Args:
        df:          OHLCV DataFrame with DatetimeIndex.
        direction:   'bullish' (buy-side lows) or 'bearish' (sell-side highs).
        ltc_type:    'rb' (rejection block) or 'ob' (order block) — passed to find_hpfs.
        weekly_open: If provided, filter out pools on the wrong side.

    Returns:
        DataFrame from find_hpfs() — columns: ltc_time, ltc_open, hpfs_time,
        hpfs_level, hpfs_bar, raid_time, raid_bar.
    """
    result = find_hpfs(df, direction, ltc_type)

    if weekly_open is not None and not result.empty:
        if direction == 'bullish':
            result = result[result['hpfs_level'] > weekly_open]
        else:
            result = result[result['hpfs_level'] < weekly_open]

    return result.reset_index(drop=True)


def find_raid_bar(
    level: float,
    direction: Literal['bullish', 'bearish'],
    df: pd.DataFrame,
    from_ts: pd.Timestamp,
) -> Optional[pd.Timestamp]:
    """
    Return the timestamp of the first candle after from_ts that raids level.

    For a buy-side pool (bullish):  raided when high[k] > level.
    For a sell-side pool (bearish): raided when low[k]  < level.

    Returns None if the level is never raided in the remaining bars.
    """
    future = df[df.index > from_ts]
    if direction == 'bullish':
        taken = future[future['high'] > level]
    else:
        taken = future[future['low'] < level]
    return taken.index[0] if len(taken) else None
