"""
SMT Divergence (Smart Money Technique)
=======================================

A crack in correlation between positively correlated instruments: one makes a new
swing extreme while the other(s) fail to confirm.

See knowledge/ict/entries/smt-divergence.md
"""

import pandas as pd
from typing import Dict, Optional

from ict.registry import concept


@concept("smt-divergence")
def detect_smt(
    correlated: Dict[str, pd.DataFrame],
    kind: str = 'high',
    swing_window: int = 3,
) -> Optional[dict]:
    """
    Detect SMT divergence across correlated instruments.

    Bullish SMT (kind='low'): one instrument makes a lower low (sweeps sell stops)
    while at least one other holds a higher low — the sweep on the leader was
    engineered, not genuine weakness.

    Bearish SMT (kind='high'): one instrument makes a higher high while at least
    one other makes a lower high.

    Args:
        correlated:   Dict of instrument name → OHLCV DataFrame (same time range).
                      Expects ES, NQ, YM per project convention.
        kind:         'high' (bearish divergence) or 'low' (bullish divergence).
        swing_window: Number of bars to look back for the prior swing extreme.

    Returns:
        dict with keys {kind, leader, diverging, leader_extreme, diverging_extreme,
        time} or None if no divergence detected.
    """
    if not correlated or len(correlated) < 2:
        return None

    extremes = {}
    prior_extremes = {}

    for name, df in correlated.items():
        if df is None or len(df) < swing_window + 1:
            return None
        if kind == 'high':
            extremes[name] = float(df['high'].iloc[-swing_window:].max())
            prior_extremes[name] = float(df['high'].iloc[-2 * swing_window:-swing_window].max())
        else:
            extremes[name] = float(df['low'].iloc[-swing_window:].min())
            prior_extremes[name] = float(df['low'].iloc[-2 * swing_window:-swing_window].min())

    if kind == 'high':
        # Bearish: leader makes higher high, diverging makes lower high
        leaders = [n for n in extremes if extremes[n] > prior_extremes[n]]
        diverging = [n for n in extremes if extremes[n] < prior_extremes[n]]
    else:
        # Bullish: leader makes lower low, diverging holds higher low
        leaders = [n for n in extremes if extremes[n] < prior_extremes[n]]
        diverging = [n for n in extremes if extremes[n] > prior_extremes[n]]

    if not leaders or not diverging:
        return None

    leader = leaders[0]
    div = diverging[0]

    # Get the timestamp from the leader's most recent extreme bar
    leader_df = correlated[leader]
    if kind == 'high':
        t = leader_df['high'].iloc[-swing_window:].idxmax()
    else:
        t = leader_df['low'].iloc[-swing_window:].idxmin()

    return {
        'kind': kind,
        'leader': leader,
        'diverging': diverging,
        'leader_extreme': extremes[leader],
        'diverging_extreme': extremes[div],
        'time': t,
    }


def smt_confirmed(
    correlated: Dict[str, pd.DataFrame],
    kind: str = 'high',
    swing_window: int = 3,
) -> bool:
    """Convenience wrapper — returns True if SMT divergence is present."""
    return detect_smt(correlated, kind, swing_window) is not None
