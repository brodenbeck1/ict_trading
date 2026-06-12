"""
Sessions & Reference Ranges
============================

Opening range, session high/low extraction, and reference range computation.

See knowledge/ict/time-and-price/sessions-and-ranges.md
"""

import pandas as pd
from typing import Optional

from ict.registry import concept
from ict.utils.time_utils import ny_index


@concept("sessions-and-ranges")
def opening_range(
    df: pd.DataFrame,
    session_date: pd.Timestamp,
    minutes: int = 30,
) -> Optional[dict]:
    """
    Compute the high/low of the NY midnight opening range on session_date.

    The opening range is the first `minutes` after 00:00 NY local time —
    the true-day open per the ICT midnight-open concept.

    Args:
        df:           Intraday OHLCV bars, DatetimeIndex.
        session_date: Calendar date of the session (tz-naive).
        minutes:      Length of the opening range window in minutes (default 30).

    Returns:
        {'high': float, 'low': float, 'open': float} or None if no bars found.
    """
    ny = ny_index(df)
    ny_min = ny.hour * 60 + ny.minute
    on_date = ny.date == session_date.date()
    in_or = on_date & (ny_min >= 0) & (ny_min < minutes)
    bars = df[in_or]
    if len(bars) == 0:
        return None
    return {
        'high':  float(bars['high'].max()),
        'low':   float(bars['low'].min()),
        'open':  float(bars['open'].iloc[0]),
    }


def session_high_low(
    df: pd.DataFrame,
    session_date: pd.Timestamp,
    start_ny: str,
    end_ny: str,
) -> Optional[dict]:
    """
    Compute the high/low of an arbitrary session window on session_date.

    Args:
        df:           Intraday OHLCV bars.
        session_date: Calendar date.
        start_ny:     Window open in 'HH:MM' NY local time.
        end_ny:       Window close in 'HH:MM' NY local time.

    Returns:
        {'high': float, 'low': float, 'start': Timestamp, 'end': Timestamp}
        or None.
    """
    ny = ny_index(df)
    ny_min = ny.hour * 60 + ny.minute
    on_date = ny.date == session_date.date()
    sh, sm = map(int, start_ny.split(':'))
    eh, em = map(int, end_ny.split(':'))
    mask = on_date & (ny_min >= sh * 60 + sm) & (ny_min < eh * 60 + em)
    bars = df[mask]
    if len(bars) == 0:
        return None
    return {
        'high':  float(bars['high'].max()),
        'low':   float(bars['low'].min()),
        'start': bars.index[0],
        'end':   bars.index[-1],
    }
