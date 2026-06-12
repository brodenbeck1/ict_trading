"""
Market Structure Analysis
========================

Identifies swing highs and swing lows based on ICT methodology.
A swing high has lower highs on both left and right sides.
A swing low has higher lows on both left and right sides.
"""

import pandas as pd
import numpy as np
from typing import List, Literal, Optional

from ict.registry import concept
from ict.utils.time_utils import localize_like


@concept("swing-points")
class SwingPointScanner:  # no depends_on — primitive
    """
    Identifies swing highs and swing lows based on ICT methodology.
    A swing high has lower highs on both left and right sides.
    A swing low has higher lows on both left and right sides.
    """
    
    def __init__(self, df: pd.DataFrame, lookback: int = 1):
        """
        Args:
            df: OHLCV DataFrame with datetime index
            lookback: Number of candles on each side to confirm swing (default=1)
        """
        self.df = df.copy()
        self.lookback = lookback
        self.swing_highs = None
        self.swing_lows = None
    
    def identify_swings(self) -> pd.DataFrame:
        """
        Identify all swing highs and swing lows in the dataset.
        Returns DataFrame with swing_high and swing_low columns.
        """
        df = self.df.copy()
        n = self.lookback
        
        # Initialize columns
        df['swing_high'] = np.nan
        df['swing_low'] = np.nan
        df['swing_high_price'] = np.nan
        df['swing_low_price'] = np.nan
        
        # Need at least (2*lookback + 1) candles to identify a swing
        if len(df) < (2 * n + 1):
            return df
        
        # Identify swing highs
        for i in range(n, len(df) - n):
            current_high = df['high'].iloc[i]
            
            # Check if all lookback candles on left have lower highs
            left_condition = all(df['high'].iloc[i - j] < current_high for j in range(1, n + 1))
            
            # Check if all lookback candles on right have lower highs
            right_condition = all(df['high'].iloc[i + j] < current_high for j in range(1, n + 1))
            
            if left_condition and right_condition:
                df.loc[df.index[i], 'swing_high'] = 1
                df.loc[df.index[i], 'swing_high_price'] = current_high
        
        # Identify swing lows
        for i in range(n, len(df) - n):
            current_low = df['low'].iloc[i]
            
            # Check if all lookback candles on left have higher lows
            left_condition = all(df['low'].iloc[i - j] > current_low for j in range(1, n + 1))
            
            # Check if all lookback candles on right have higher lows
            right_condition = all(df['low'].iloc[i + j] > current_low for j in range(1, n + 1))
            
            if left_condition and right_condition:
                df.loc[df.index[i], 'swing_low'] = 1
                df.loc[df.index[i], 'swing_low_price'] = current_low
        
        self.swing_highs = df[df['swing_high'] == 1].copy()
        self.swing_lows = df[df['swing_low'] == 1].copy()
        
        return df
    
    def get_recent_swings(self, n: int = 5, swing_type: Literal['high', 'low', 'both'] = 'both') -> pd.DataFrame:
        """
        Get the most recent N swing points.
        
        Args:
            n: Number of recent swings to return
            swing_type: 'high', 'low', or 'both'
        
        Returns:
            DataFrame with recent swing points
        """
        if self.swing_highs is None or self.swing_lows is None:
            self.identify_swings()
        
        if swing_type == 'high':
            return self.swing_highs.tail(n)
        elif swing_type == 'low':
            return self.swing_lows.tail(n)
        else:
            # Combine and sort by index
            combined = pd.concat([
                self.swing_highs[['high', 'swing_high', 'swing_high_price']],
                self.swing_lows[['low', 'swing_low', 'swing_low_price']]
            ]).sort_index()
            return combined.tail(n)
    
    def get_liquidity_levels(self) -> dict:
        """
        Extract liquidity levels from swing points.
        Returns dict with buy_stops (above swing highs) and sell_stops (below swing lows).
        """
        if self.swing_highs is None or self.swing_lows is None:
            self.identify_swings()
        
        return {
            'buy_stops': self.swing_highs['swing_high_price'].dropna().tolist(),
            'sell_stops': self.swing_lows['swing_low_price'].dropna().tolist()
        }
    
    def find_relative_equal_highs(self, tolerance: float = 0.0005) -> list:
        """
        Find clusters of swing highs that are relatively equal (within tolerance).
        
        Args:
            tolerance: Percentage tolerance for equality (default 0.05% for futures)
        
        Returns:
            List of dicts: {'price', 'timestamps', 'count', 'min_price', 'max_price'}
        """
        if self.swing_highs is None:
            self.identify_swings()
        
        highs = self.swing_highs['swing_high_price'].dropna()
        if len(highs) < 2:
            return []
        
        clusters = []
        used_indices = set()
        
        for i, (idx, price) in enumerate(highs.items()):
            if i in used_indices:
                continue
            
            # Find all highs within tolerance
            tolerance_range = price * tolerance
            similar_highs = highs[
                (highs >= price - tolerance_range) & 
                (highs <= price + tolerance_range)
            ]
            
            if len(similar_highs) >= 2:
                clusters.append({
                    'price': similar_highs.mean(),
                    'timestamps': similar_highs.index.tolist(),
                    'count': len(similar_highs),
                    'min_price': similar_highs.min(),
                    'max_price': similar_highs.max()
                })
                
                # Mark these indices as used
                for idx in similar_highs.index:
                    used_indices.add(highs.index.get_loc(idx))
        
        return clusters
    
    def find_relative_equal_lows(self, tolerance: float = 0.0005) -> list:
        """
        Find clusters of swing lows that are relatively equal (within tolerance).
        
        Args:
            tolerance: Percentage tolerance for equality (default 0.05% for futures)
        
        Returns:
            List of dicts: {'price', 'timestamps', 'count', 'min_price', 'max_price'}
        """
        if self.swing_lows is None:
            self.identify_swings()
        
        lows = self.swing_lows['swing_low_price'].dropna()
        if len(lows) < 2:
            return []
        
        clusters = []
        used_indices = set()
        
        for i, (idx, price) in enumerate(lows.items()):
            if i in used_indices:
                continue
            
            # Find all lows within tolerance
            tolerance_range = price * tolerance
            similar_lows = lows[
                (lows >= price - tolerance_range) & 
                (lows <= price + tolerance_range)
            ]
            
            if len(similar_lows) >= 2:
                clusters.append({
                    'price': similar_lows.mean(),
                    'timestamps': similar_lows.index.tolist(),
                    'count': len(similar_lows),
                    'min_price': similar_lows.min(),
                    'max_price': similar_lows.max()
                })
                
                # Mark these indices as used
                for idx in similar_lows.index:
                    used_indices.add(lows.index.get_loc(idx))

        return clusters


# ---------------------------------------------------------------------------
# Market Structure Shift (MSS / CHoCH)
# See knowledge/ict/market-structure/market-structure-shift.md
# ---------------------------------------------------------------------------

@concept("market-structure-shift", depends_on=["swing-points"])
def detect_mss(
    df: pd.DataFrame,
    direction: str,
    swing_lookback: int = 3,
    max_bars_after_sweep: int = 30,
    sweep_time: Optional[pd.Timestamp] = None,
) -> Optional[dict]:
    """
    Detect a Market Structure Shift (MSS / CHoCH).

    A counter-trend break of the most recent opposing swing level, ideally with
    displacement, following a liquidity sweep. This is the confirmation step in the
    entry sequence: sweep → MSS → retrace → deliver.

    Args:
        df:                   Intraday OHLCV bars (1m/3m/5m).
        direction:            'bearish' — price breaks a swing low after sweeping highs;
                              'bullish' — price breaks a swing high after sweeping lows.
        swing_lookback:       Bar lookback for SwingPointScanner.
        max_bars_after_sweep: If sweep_time given, only consider breaks within this
                              many bars after the sweep.
        sweep_time:           Optional timestamp of the preceding sweep; used to
                              time-link the MSS.

    Returns:
        dict with keys {direction, broken_level, break_time, sweep_ref, bar_index}
        or None if no MSS detected.
    """
    if df is None or len(df) < swing_lookback * 2 + 1:
        return None

    # Swing detection must only use bars up to (and including) the sweep so the
    # pivot is established BEFORE the MSS search window, not from future bars.
    if sweep_time is not None:
        cutoff = df.index.get_indexer([sweep_time], method='nearest')[0]
        pre_df = df.iloc[: cutoff + 1]
        end    = min(cutoff + max_bars_after_sweep + 1, len(df))
        search_df = df.iloc[cutoff:end]
    else:
        pre_df    = df
        search_df = df

    if len(pre_df) < swing_lookback * 2 + 1:
        return None

    scanner = SwingPointScanner(pre_df, lookback=swing_lookback)
    scanner.identify_swings()

    if direction == 'bearish':
        lows = (scanner.swing_lows['swing_low_price'].dropna()
                if scanner.swing_lows is not None else pd.Series(dtype=float))
        if len(lows) == 0:
            return None
        pivot_low = float(lows.iloc[-1])
        pivot_time = lows.index[-1]

        for i in range(len(search_df)):
            bar = search_df.iloc[i]
            t   = search_df.index[i]
            if t <= pivot_time:
                continue
            if bar['close'] < pivot_low:
                return {
                    'direction': 'bearish',
                    'broken_level': pivot_low,
                    'break_time': t,
                    'sweep_ref': sweep_time,
                    'bar_index': df.index.get_indexer([t], method='nearest')[0],
                }
    else:
        highs = (scanner.swing_highs['swing_high_price'].dropna()
                 if scanner.swing_highs is not None else pd.Series(dtype=float))
        if len(highs) == 0:
            return None
        pivot_high = float(highs.iloc[-1])
        pivot_time = highs.index[-1]

        for i in range(len(search_df)):
            bar = search_df.iloc[i]
            t   = search_df.index[i]
            if t <= pivot_time:
                continue
            if bar['close'] > pivot_high:
                return {
                    'direction': 'bullish',
                    'broken_level': pivot_high,
                    'break_time': t,
                    'sweep_ref': sweep_time,
                    'bar_index': df.index.get_indexer([t], method='nearest')[0],
                }

    return None


# ---------------------------------------------------------------------------
# Relative Equal Highs / Lows
# See knowledge/ict/liquidity/relative-equal-highs-lows.md
# ---------------------------------------------------------------------------

@concept("relative-equal-highs-lows", depends_on=["swing-points"])
def find_relative_equal_levels(
    df: pd.DataFrame,
    before: pd.Timestamp,
    side: str,
    lookback_days: int = 5,
    tolerance_pts: float = 5.0,
    swing_lookback: int = 1,
) -> List[dict]:
    """
    Find untested swing highs (side='highs') or lows (side='lows') within a
    rolling lookback window that form relative-equal clusters — resting stop shelves.

    A cluster is only returned if EVERY member is still resting: if any member
    was traded through since it formed (its liquidity already run), the whole
    cluster is discarded — a later equal swing does not revive run liquidity.

    Args:
        df:            15m (or lower) OHLCV bars.
        before:        Upper time bound — only use bars strictly before this time.
        side:          'highs' (buy-side pools) or 'lows' (sell-side pools).
        lookback_days: Days back from `before` to scan.
        tolerance_pts: Max price distance between touches to form a cluster.
        swing_lookback: Bar lookback for SwingPointScanner.

    Returns:
        List of dicts: {price, extreme_price, inner_price, timestamps, count}.
        Sorted by extreme_price descending (highs) or ascending (lows).
    """
    before = localize_like(before, df.index)
    start  = before - pd.Timedelta(days=lookback_days)
    window = df[(df.index >= start) & (df.index < before)].copy()
    if len(window) < 3:
        return []

    scanner = SwingPointScanner(window, lookback=swing_lookback)
    scanner.identify_swings()

    if side == 'highs':
        if scanner.swing_highs is None or len(scanner.swing_highs) == 0:
            return []
        prices    = scanner.swing_highs['swing_high_price'].dropna()
        extreme_fn, inner_fn = max, min
    else:
        if scanner.swing_lows is None or len(scanner.swing_lows) == 0:
            return []
        prices    = scanner.swing_lows['swing_low_price'].dropna()
        extreme_fn, inner_fn = min, max

    def member_taken(ts_m: pd.Timestamp, price_m: float) -> bool:
        """A member is taken if price traded beyond it after it formed."""
        after = window[window.index > ts_m]
        if len(after) == 0:
            return False
        return after['high'].max() > price_m if side == 'highs' else after['low'].min() < price_m

    clusters: List[dict] = []
    used: set = set()

    for i, (ts, price) in enumerate(prices.items()):
        if i in used:
            continue
        similar = prices[(prices >= price - tolerance_pts) & (prices <= price + tolerance_pts)]
        for j, idx in enumerate(prices.index):
            if idx in similar.index:
                used.add(j)

        # Relative-equal liquidity is only valid if EVERY member is still resting.
        # A single member raided since its own formation means the shelf has
        # already been run — even if a later equal swing reprinted the level.
        if any(member_taken(t, float(p)) for t, p in similar.items()):
            continue

        clusters.append({
            'price':         float(similar.mean()),
            'extreme_price': float(extreme_fn(similar.values)),
            'inner_price':   float(inner_fn(similar.values)),
            'timestamps':    similar.index.tolist(),
            'count':         int(len(similar)),
        })

    if side == 'highs':
        clusters.sort(key=lambda c: c['extreme_price'], reverse=True)
    else:
        clusters.sort(key=lambda c: c['extreme_price'])

    return clusters
