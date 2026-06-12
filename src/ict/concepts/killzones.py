"""
Killzones
=========

Boolean bar masks for the recurring institutional order-flow windows.
Time gates price — the same pattern outside a killzone is not the same trade.

See knowledge/ict/time-and-price/killzones.md
"""

import pandas as pd
from typing import List, Tuple

from ict.registry import concept
from ict.utils.time_utils import ny_index

# Default windows in NY local time (HH:MM, HH:MM)
LONDON_KZ    = ('02:00', '05:00')
NY_AM_KZ     = ('08:30', '11:00')
NY_PM_KZ     = ('13:30', '16:00')
LONDON_CLOSE = ('10:00', '12:00')
ASIA_KZ      = ('19:00', '22:00')


@concept("killzones")
def session_mask(
    df: pd.DataFrame,
    session_date: pd.Timestamp,
    killzones: List[Tuple[str, str]],
) -> pd.Series:
    """
    Build a boolean mask over df.index selecting bars that fall inside any of
    the specified killzone windows on session_date, in NY local time.

    DST is handled automatically via America/New_York — never pass hardcoded
    UTC offsets.

    Args:
        df:           OHLCV DataFrame with DatetimeIndex (UTC or tz-naive UTC).
        session_date: The calendar date of the session (tz-naive local date).
        killzones:    List of ('HH:MM', 'HH:MM') NY-time window pairs.

    Returns:
        Boolean pd.Series aligned to df.index.
    """
    ny = ny_index(df)
    ny_min = ny.hour * 60 + ny.minute
    on_date = ny.date == session_date.date()
    mask = pd.Series(False, index=df.index)

    for start, end in killzones:
        sh, sm = map(int, start.split(':'))
        eh, em = map(int, end.split(':'))
        window = (ny_min >= sh * 60 + sm) & (ny_min < eh * 60 + em)
        mask = mask | pd.Series(on_date & window, index=df.index)

    return mask


def in_killzone(
    ts: pd.Timestamp,
    killzones: List[Tuple[str, str]],
) -> bool:
    """Return True if a single timestamp falls inside any killzone window."""
    if ts.tz is None:
        ts = ts.tz_localize('UTC')
    ny = ts.tz_convert('America/New_York')
    ny_min = ny.hour * 60 + ny.minute
    for start, end in killzones:
        sh, sm = map(int, start.split(':'))
        eh, em = map(int, end.split(':'))
        if sh * 60 + sm <= ny_min < eh * 60 + em:
            return True
    return False
