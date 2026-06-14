"""
Dark Pool Detection
====================

A Dark Pool is an implied imbalance zone that forms when price trades through a
no-liquidity swing point WITHOUT leaving a formal Fair Value Gap.

The zone spans from the no-liquidity swing level to the low (bullish) or high
(bearish) of the first candle that clears the swing — the hidden area where
delivery occurred but no explicit FVG marks it.

Complements the Break Away Gap (BAG):
  BAG        — displacement through no-liq swing WITH an FVG
  Dark Pool  — displacement through no-liq swing WITHOUT an FVG

See knowledge/currency-merchant/price-action/dark-pool.md
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import Literal

from ict.registry import concept
from ict.concepts.market_structure import SwingPointScanner
from ict.concepts.pool_validity import classify_swing_liquidity
from ict.concepts.break_away_gap import find_break_away_gaps


@dataclass
class DarkPool:
    timestamp: pd.Timestamp    # timestamp of the displacement candle
    direction: str             # 'bullish' or 'bearish'
    top: float                 # top of the dark pool zone
    bottom: float              # bottom of the dark pool zone
    swept_level: float         # the no-liquidity swing point cleared
    swept_ts: pd.Timestamp     # timestamp of that swing point


@concept("dark-pool", depends_on=["swing-without-liquidity", "fair-value-gap"])
def find_dark_pools(
    df: pd.DataFrame,
    direction: Literal['bullish', 'bearish'],
    swing_lookback: int = 1,
) -> list[DarkPool]:
    """
    Find all Dark Pools in df.

    A Dark Pool forms when price trades through a no-liquidity swing point
    without leaving a formal FVG (as opposed to a Break Away Gap, which does).

    Bullish Dark Pool zone: [no_liq_swing_high, displacement_candle.low]
    Bearish Dark Pool zone: [displacement_candle.high, no_liq_swing_low]

    Args:
        df:             OHLCV DataFrame with DatetimeIndex.
        direction:      'bullish' or 'bearish'.
        swing_lookback: bars each side to confirm a swing point.

    Returns:
        List of DarkPool, chronological.
    """
    scanner = SwingPointScanner(df, lookback=swing_lookback)
    scanner.identify_swings()

    if direction == 'bullish':
        swings = scanner.swing_highs[['swing_high_price']].dropna()
        classified = classify_swing_liquidity(swings, 'high')
        no_liq = classified[classified['classification'] == 'no_liquidity']
        price_col = 'swing_high_price'
    else:
        swings = scanner.swing_lows[['swing_low_price']].dropna()
        classified = classify_swing_liquidity(swings, 'low')
        no_liq = classified[classified['classification'] == 'no_liquidity']
        price_col = 'swing_low_price'

    # A no-liq swing that already produced a BAG cannot also produce a Dark Pool.
    # Also, if the clearing candle is the same as any BAG's FVG center, it HAS an FVG
    # (by definition) so the whole displacement is a BAG move — not a dark pool.
    bags = find_break_away_gaps(df, direction, swing_lookback)
    bag_swept_ts: set[pd.Timestamp] = {b.swept_ts for b in bags}
    bag_fvg_ts: set[pd.Timestamp]   = {b.fvg.timestamp for b in bags}

    results: list[DarkPool] = []
    consumed: set[pd.Timestamp] = set()

    for swing_ts, swing_row in no_liq.iterrows():
        if swing_ts in consumed or swing_ts in bag_swept_ts:
            continue

        level = swing_row[price_col]
        future = df[df.index > swing_ts]

        # First candle that fully clears the swing (its low/high sits past the level)
        if direction == 'bullish':
            cleared = future[future['low'] > level]
        else:
            cleared = future[future['high'] < level]

        if cleared.empty:
            continue

        disp_ts  = cleared.index[0]

        # If the clearing candle is itself a BAG's displacement, it has an FVG —
        # the move is a BAG, not a dark pool.
        if disp_ts in bag_fvg_ts:
            continue

        disp     = df.loc[disp_ts]

        if direction == 'bullish':
            zone_bottom = level
            zone_top    = float(disp['low'])
        else:
            zone_bottom = float(disp['high'])
            zone_top    = level

        results.append(DarkPool(
            timestamp=disp_ts,
            direction=direction,
            top=zone_top,
            bottom=zone_bottom,
            swept_level=level,
            swept_ts=swing_ts,
        ))
        consumed.add(swing_ts)

    return results
