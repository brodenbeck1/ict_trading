"""
Data Loading Utilities
======================

Handles loading and resampling of futures data from CSV files.
"""

import re
import pandas as pd
from pathlib import Path
from typing import Optional, Literal


def _normalize_freq(tf: str) -> str:
    """Normalize legacy pandas offset aliases for pandas >= 2.2.

    Keeps the project's documented timeframe API ('1T', '5T', '15T', '1H', '4H')
    working after pandas removed the 'T' (minute) and 'H' (hour) aliases in
    favour of 'min' and 'h'.
    """
    tf = re.sub(r'(\d*)T$', r'\1min', tf)
    tf = re.sub(r'(\d*)H$', r'\1h', tf)
    return tf


class DataLoader:
    """
    Load and resample futures data from CSV files.
    
    Supports NQ, ES, and YM futures with flexible timeframe resampling.
    """
    
    def __init__(self, timeframe: str, weeks: Optional[int] = None, data_dir: Optional[str] = None):
        """
        Initialize data loader.
        
        Args:
            timeframe: Pandas resample string ('5T', '15T', '1H', 'D', etc.)
            weeks: Number of weeks to load (None = all data)
            data_dir: Path to data directory (defaults to standard location)
        """
        self.timeframe = timeframe
        self.weeks = weeks
        
        if data_dir is None:
            self.data_dir = Path.home() / 'Projects' / 'Data'
        else:
            self.data_dir = Path(data_dir)
    
    def _load_and_resample(self, symbol: Literal['NQ', 'ES', 'YM']) -> pd.DataFrame:
        """
        Internal method to load and resample data.
        
        Args:
            symbol: Futures symbol to load
        
        Returns:
            Resampled OHLCV DataFrame with datetime index
        """
        # Map symbol to filename
        filename_map = {
            'NQ': 'nq_futures_1m_cleaned.csv',
            'ES': 'es_futures_1m_cleaned.csv',
            'YM': 'ym_futures_1m_cleaned.csv',
            'DXY_DAILY': 'dxy_daily.csv',
            'DXY_1H': 'dxy_1h.csv',
        }
        
        filepath = self.data_dir / filename_map[symbol]
        
        if not filepath.exists():
            raise FileNotFoundError(f"Data file not found: {filepath}")
        
        # Load data
        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp').sort_index()
        
        # Filter by weeks if specified
        if self.weeks is not None:
            cutoff_date = df.index.max() - pd.Timedelta(weeks=self.weeks)
            df = df[df.index >= cutoff_date]
        
        # Resample to specified timeframe
        agg = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        resampled = df.resample(_normalize_freq(self.timeframe)).agg(agg)
        return resampled
    
    def read_NQ(self) -> pd.DataFrame:
        """Load Nasdaq 100 futures (NQ) data."""
        return self._load_and_resample('NQ')
    
    def read_ES(self) -> pd.DataFrame:
        """Load S&P 500 futures (ES) data."""
        return self._load_and_resample('ES')
    
    def read_YM(self) -> pd.DataFrame:
        """Load Dow Jones futures (YM) data."""
        return self._load_and_resample('YM')
    
    def read_DXY(self, resolution: str = 'daily') -> pd.DataFrame:
        """Load DXY (US Dollar Index) data.

        Args:
            resolution: 'daily' (2010–present) or '1h' (last ~730 days).
        """
        key = 'DXY_DAILY' if resolution == 'daily' else 'DXY_1H'
        filepath = self.data_dir / {'DXY_DAILY': 'dxy_daily.csv', 'DXY_1H': 'dxy_1h.csv'}[key]
        if not filepath.exists():
            raise FileNotFoundError(
                f"DXY data not found at {filepath}. "
                "Run scripts/fetch_dxy.py to download."
            )
        df = pd.read_csv(filepath, index_col='timestamp', parse_dates=True)
        df = df.sort_index()
        if self.weeks is not None:
            cutoff = df.index.max() - pd.Timedelta(weeks=self.weeks)
            df = df[df.index >= cutoff]
        return df

    def read_all(self) -> dict:
        """
        Load all available futures data.
        
        Returns:
            Dict with keys 'NQ', 'ES', 'YM' containing respective DataFrames
        """
        return {
            'NQ': self.read_NQ(),
            'ES': self.read_ES(),
            'YM': self.read_YM()
        }


# Maintain backward compatibility with old class name
class csvReader(DataLoader):
    """Deprecated: Use DataLoader instead. Maintained for backward compatibility."""
    pass
