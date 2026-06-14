"""
Break Away Gap (BAG) Detection
================================

A Break Away Gap is an FVG whose displacement candle traded through a
no-liquidity swing point (a swing whose extreme already consumed the prior
swing's liquidity).

See knowledge/currency-merchant/price-action/break-away-gap.md
"""

from __future__ import annotations

import pandas as pd
from dataclasses import dataclass
from typing import Literal

from ict.registry import concept
from ict.concepts.fair_value_gap import find_fvgs, FVG
from ict.concepts.market_structure import SwingPointScanner
from ict.concepts.pool_validity import classify_swing_liquidity


@dataclass
class BreakAwayGap:
    fvg: FVG                    # the underlying Fair Value Gap
    swept_level: float          # the no-liquidity swing point that was broken through
    swept_ts: pd.Timestamp      # timestamp of that swing point


@concept("break-away-gap", depends_on=["fair-value-gap", "swing-without-liquidity"])
def find_break_away_gaps(
    df: pd.DataFrame,
    direction: Literal['bullish', 'bearish'],
    swing_lookback: int = 1,
) -> list[BreakAwayGap]:
    """
    Find all Break Away Gaps in df.

    A BAG is an FVG whose displacement candle traded through a no-liquidity
    swing point in the same direction.

    Args:
        df:             OHLCV DataFrame with DatetimeIndex.
        direction:      'bullish' (displacement broke through a no-liquidity
                        swing high) or 'bearish' (broke through a no-liquidity
                        swing low).
        swing_lookback: lookback passed to SwingPointScanner.

    Returns:
        List of BreakAwayGap, chronological.
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

    fvgs = find_fvgs(df, direction)
    results: list[BreakAwayGap] = []

    consumed: set[pd.Timestamp] = set()

    for fvg in fvgs:
        prior_no_liq = no_liq[no_liq.index < fvg.timestamp]
        if prior_no_liq.empty:
            continue

        # Only the MOST RECENTLY formed no-liquidity swing is the relevant one.
        # If that swing is already consumed, no BAG forms here.
        swing_ts  = prior_no_liq.index[-1]
        swing_row = prior_no_liq.iloc[-1]
        level     = swing_row[price_col]

        if swing_ts in consumed:
            continue

        # The FVG gap must reach the swing level:
        #   Bullish: gap top  (candle[i+1].low)  >= swing high
        #   Bearish: gap bottom (candle[i+1].high) <= swing low
        if direction == 'bullish':
            gap_reaches = fvg.top >= level
        else:
            gap_reaches = fvg.bottom <= level

        if gap_reaches:
            results.append(BreakAwayGap(fvg=fvg, swept_level=level, swept_ts=swing_ts))
            consumed.add(swing_ts)

    return results
