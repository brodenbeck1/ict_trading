"""
Liquidity Sweep / Stop Hunt
===========================

Price trades beyond a liquidity pool, triggers resting stops, then reverses back
inside. The rejection distinguishes a sweep (reversal signal) from a run (continuation).

See knowledge/ict/liquidity/liquidity-sweep-stop-hunt.md
"""

import pandas as pd
from typing import Optional

from ict.registry import concept


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
