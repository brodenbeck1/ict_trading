"""
Timezone helpers shared across concepts and models.

All ICT time logic runs in America/New_York (DST-aware). Data is stored UTC.
"""

import pandas as pd


def localize_like(ts: pd.Timestamp, ref: pd.DatetimeIndex) -> pd.Timestamp:
    """Match ts tz-awareness to ref index (tz-aware or tz-naive)."""
    if ref.tz is not None and ts.tz is None:
        return ts.tz_localize(ref.tz)
    if ref.tz is None and ts.tz is not None:
        return ts.replace(tzinfo=None)
    return ts


def ny_index(df: pd.DataFrame) -> pd.DatetimeIndex:
    """Return df.index converted to America/New_York. Treats tz-naive as UTC."""
    idx = df.index
    if idx.tz is None:
        idx = idx.tz_localize('UTC')
    return idx.tz_convert('America/New_York')
