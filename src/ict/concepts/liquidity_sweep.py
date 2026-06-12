"""
Liquidity Sweep / Stop Hunt
===========================

Price trades beyond a liquidity pool, triggers resting stops, then reverses back
inside. The rejection distinguishes a sweep (reversal signal) from a run (continuation).

See knowledge/ict/liquidity/liquidity-sweep-stop-hunt.md
"""

import pandas as pd
from typing import Optional, Tuple

from ict.registry import concept
from ict.utils.time_utils import localize_like


def first_breach(
    df: pd.DataFrame,
    level: float,
    side: str,
    after: Optional[pd.Timestamp] = None,
) -> Tuple[Optional[pd.Timestamp], Optional[pd.Series]]:
    """
    Find the first bar that trades *beyond* a liquidity level.

    The first breach is the moment the resting liquidity at `level` is taken.
    Any later trade through the same level is price revisiting an already-
    mitigated pool — not a fresh liquidity grab. This is the canonical rule for
    deciding whether a pool is still "live": a pool is only valid as a sweep
    target if it has NOT been breached between its formation and the moment of
    interest.

    Args:
        df:     OHLCV bars, DatetimeIndex.
        level:  The pool price.
        side:   'high' — buy-side pool, breached when a bar's high > level;
                'low'  — sell-side pool, breached when a bar's low  < level.
        after:  Only consider bars strictly after this timestamp (the pool's
                formation time). None scans the whole frame.

    Returns:
        (timestamp, row) of the first breaching bar, or (None, None).
    """
    if df is None or len(df) == 0:
        return None, None
    sub = df
    if after is not None:
        after = localize_like(pd.Timestamp(after), df.index)
        sub = df[df.index > after]
    hit = sub[sub['high'] > level] if side == 'high' else sub[sub['low'] < level]
    if len(hit) == 0:
        return None, None
    return hit.index[0], hit.iloc[0]


def pool_is_live(
    df: pd.DataFrame,
    level: float,
    side: str,
    formed_at: Optional[pd.Timestamp],
    as_of: pd.Timestamp,
) -> bool:
    """
    True if `level`'s liquidity is still resting at `as_of` — i.e. it was not
    already breached between `formed_at` and `as_of`. A pool taken earlier is
    dead and must not be treated as a sweep target.
    """
    ts, _ = first_breach(df, level, side, after=formed_at)
    if ts is None:
        return True
    return ts >= localize_like(pd.Timestamp(as_of), df.index)


@concept("liquidity-sweep-stop-hunt")
def detect_liquidity_sweep(
    df: pd.DataFrame,
    level: float,
    direction: str,
    rejection_window_bars: int = 12,
) -> Optional[dict]:
    """
    Detect a liquidity sweep of a price level.

    A sweep requires: price trades through the level (triggering stops) AND closes
    back inside within `rejection_window_bars`. If price closes beyond the level and
    stays, it's classified as a run (continuation), not a sweep.

    Args:
        df:                     OHLCV bars, DatetimeIndex.
        level:                  The pool price being tested.
        direction:              'high' — testing a buy-side level (high > level);
                                'low'  — testing a sell-side level (low < level).
        rejection_window_bars:  Max bars after the breach for a close-back-inside.

    Returns:
        dict with keys {level, direction, sweep_bar, sweep_time, depth, classification}
        or None if no sweep found.
    """
    if df is None or len(df) < 2:
        return None

    for i in range(len(df)):
        bar = df.iloc[i]

        if direction == 'high':
            breached = bar['high'] > level
        else:
            breached = bar['low'] < level

        if not breached:
            continue

        depth = (bar['high'] - level if direction == 'high' else level - bar['low'])
        sweep_time = df.index[i]

        # Check if price closes back inside within the rejection window
        window_end = min(i + rejection_window_bars + 1, len(df))
        rejection_bars = df.iloc[i:window_end]

        if direction == 'high':
            closed_inside = (rejection_bars['close'] < level).any()
        else:
            closed_inside = (rejection_bars['close'] > level).any()

        # A run: price closes beyond and stays for >= 3 consecutive bars
        if direction == 'high':
            acceptance = (rejection_bars['close'] >= level).sum() >= 3
        else:
            acceptance = (rejection_bars['close'] <= level).sum() >= 3

        classification = 'run' if acceptance else ('sweep' if closed_inside else 'pending')

        return {
            'level': level,
            'direction': direction,
            'sweep_bar': i,
            'sweep_time': sweep_time,
            'depth': depth,
            'classification': classification,
        }

    return None


def classify_sweep_or_run(
    df: pd.DataFrame,
    level: float,
    direction: str,
    rejection_window_bars: int = 12,
    acceptance_bars: int = 3,
) -> str:
    """
    Simplified classifier: returns 'sweep', 'run', or 'none'.
    """
    result = detect_liquidity_sweep(df, level, direction, rejection_window_bars)
    if result is None:
        return 'none'
    return result['classification']
