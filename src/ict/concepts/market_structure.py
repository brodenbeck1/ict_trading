"""
Market Structure Analysis
========================

Identifies swing highs and swing lows based on ICT methodology.
A swing high has lower highs on both left and right sides.
A swing low has higher lows on both left and right sides.
"""

import pandas as pd
import numpy as np
from typing import Literal


class SwingPointScanner:
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
