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
    start_ny: str = '09:30',
) -> Optional[dict]:
    """
    Compute the high/low of the NY opening range on session_date.

    Defaults to the RTH opening range: the first `minutes` after the 09:30 NY
    cash open. `start_ny` can anchor the range to another session open (e.g.
    '08:30' for the NY session open). Note: the midnight open (00:00 NY) is a
    single reference PRICE — the true-day open, not a range — and belongs to the
    true-day-midnight-open concept, not here.

    Args:
        df:           Intraday OHLCV bars, DatetimeIndex.
        session_date: Calendar date of the session (tz-naive).
        minutes:      Length of the opening range window in minutes (default 30).
        start_ny:     Window start in 'HH:MM' NY local time (default '09:30').

    Returns:
        {'high': float, 'low': float, 'open': float} or None if no bars found.
    """
    ny = ny_index(df)
    ny_min = ny.hour * 60 + ny.minute
    sh, sm = map(int, start_ny.split(':'))
    start_min = sh * 60 + sm
    on_date = ny.date == session_date.date()
    in_or = on_date & (ny_min >= start_min) & (ny_min < start_min + minutes)
    bars = df[in_or]
    if len(bars) == 0:
        return None
    return {
        'high':        float(bars['high'].max()),
        'low':         float(bars['low'].min()),
        'open':        float(bars['open'].iloc[0]),
        'high_time':   bars['high'].idxmax(),
        'low_time':    bars['low'].idxmin(),
        'range_start': bars.index[0],
        'range_end':   bars.index[-1],
    }


def ons_range(
    df: pd.DataFrame,
    session_date: pd.Timestamp,
) -> Optional[dict]:
    """
    Compute the high/low of the Overnight Session (ONS) on session_date.

    ONS: 05:00–09:15 NY — the pre-market window bridging globex overnight to
    the RTH open. Its high/low are intraday liquidity pools; see
    knowledge/ict/time-and-price/sessions-and-ranges.md.
    """
    return session_high_low(df, session_date, start_ny='05:00', end_ny='09:15')


def chicago_range(
    df: pd.DataFrame,
    session_date: pd.Timestamp,
) -> Optional[dict]:
    """
    Compute the high/low of the Chicago session range on session_date.

    Chicago: 09:15–12:00 NY — CME pit session open through midday. Its high/low
    become liquidity pools once the window closes (formed_at = range_end). Can be
    swept same-day in the PM killzone (13:30–16:00 NY), or carried to the next day
    as a standing pool alongside PDH/PDL; see
    knowledge/ict/time-and-price/sessions-and-ranges.md.
    """
    return session_high_low(df, session_date, start_ny='09:15', end_ny='12:00')


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
