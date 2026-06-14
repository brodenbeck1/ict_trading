"""
Tests for pool_validity.py — hpfs_pools() and find_raid_bar().

hpfs_pools wraps find_hpfs() (LTC → inside-body scan), so tests verify the
weekly_open filter and that the underlying HPFS logic flows through correctly.
find_raid_bar is a standalone utility tested independently.
"""

import pandas as pd
import numpy as np
import pytest

from ict.concepts.pool_validity import hpfs_pools, find_raid_bar


def make_ohlcv(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame with a DatetimeIndex."""
    if not rows:
        idx = pd.DatetimeIndex([])
        return pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'], index=idx)
    idx = pd.date_range('2024-01-01', periods=len(rows), freq='D')
    df = pd.DataFrame(rows, index=idx)
    for col in ('open', 'high', 'low', 'close'):
        df[col] = df[col].astype(float)
    df['volume'] = 1000.0
    return df


# ── hpfs_pools ────────────────────────────────────────────────────────────────

class TestHpfsPools:

    def test_returns_dataframe_with_expected_columns(self):
        # Minimal OB bearish LTC: close[1] > high[0]; then inside-body candle
        df = make_ohlcv([
            {'open': 100, 'high': 102, 'low': 98,  'close': 101},  # bar 0
            {'open': 100, 'high': 106, 'low': 99,  'close': 105},  # bar 1 — OB LTC bearish (close > high[0])
            {'open': 103, 'high': 99,  'low': 97,  'close': 98},   # bar 2 — high(99) < open(100) → HPFS
            {'open': 98,  'high': 98,  'low': 95,  'close': 96},   # bar 3
        ])
        result = hpfs_pools(df, 'bearish', ltc_type='ob')
        assert isinstance(result, pd.DataFrame)
        for col in ('ltc_time', 'hpfs_time', 'hpfs_level', 'raid_time'):
            assert col in result.columns

    def test_bearish_ob_detects_hpfs_high(self):
        df = make_ohlcv([
            {'open': 100, 'high': 102, 'low': 98,  'close': 101},
            {'open': 100, 'high': 106, 'low': 99,  'close': 105},  # OB LTC
            {'open': 103, 'high': 99,  'low': 97,  'close': 98},   # HPFS: high(99) < ltc_open(100)
            {'open': 98,  'high': 98,  'low': 95,  'close': 96},
        ])
        result = hpfs_pools(df, 'bearish', ltc_type='ob')
        assert len(result) >= 1
        assert result.iloc[0]['hpfs_level'] == pytest.approx(99.0)

    def test_bullish_rb_detects_hpfs_low(self):
        # RB bullish LTC: low[i] < low[i-1] AND close[i] > low[i-1]
        # HPFS scan: low[j] > ltc_open (strictly greater)
        df = make_ohlcv([
            {'open': 102, 'high': 104, 'low': 100, 'close': 103},
            {'open': 101, 'high': 104, 'low': 97,  'close': 101},  # RB LTC: low(97)<100, close(101)>100; open=101
            {'open': 102, 'high': 104, 'low': 103, 'close': 104},  # low(103) > ltc_open(101) → HPFS
            {'open': 104, 'high': 106, 'low': 102, 'close': 105},
        ])
        result = hpfs_pools(df, 'bullish', ltc_type='rb')
        assert len(result) >= 1
        assert result.iloc[0]['hpfs_level'] == pytest.approx(103.0)

    def test_weekly_open_filter_bearish(self):
        # Bearish week: only HPFS highs BELOW weekly_open qualify
        df = make_ohlcv([
            {'open': 100, 'high': 102, 'low': 98,  'close': 101},
            {'open': 100, 'high': 106, 'low': 99,  'close': 105},  # OB LTC
            {'open': 103, 'high': 99,  'low': 97,  'close': 98},   # HPFS level = 99
            {'open': 98,  'high': 98,  'low': 95,  'close': 96},
        ])
        # weekly_open=98 → hpfs_level(99) is NOT below 98 → filtered out
        result_filtered = hpfs_pools(df, 'bearish', ltc_type='ob', weekly_open=98)
        # weekly_open=100 → hpfs_level(99) < 100 → passes
        result_passes = hpfs_pools(df, 'bearish', ltc_type='ob', weekly_open=100)
        assert len(result_filtered) == 0
        assert len(result_passes) >= 1

    def test_weekly_open_filter_bullish(self):
        df = make_ohlcv([
            {'open': 102, 'high': 104, 'low': 100, 'close': 103},
            {'open': 101, 'high': 104, 'low': 97,  'close': 101},  # RB LTC; open=101
            {'open': 102, 'high': 104, 'low': 103, 'close': 104},  # HPFS level = 103
            {'open': 104, 'high': 106, 'low': 102, 'close': 105},
        ])
        # Bullish week: only pools ABOVE weekly_open qualify
        result_filtered = hpfs_pools(df, 'bullish', ltc_type='rb', weekly_open=104)
        result_passes   = hpfs_pools(df, 'bullish', ltc_type='rb', weekly_open=100)
        assert len(result_filtered) == 0
        assert len(result_passes) >= 1

    def test_empty_df_returns_empty(self):
        df = make_ohlcv([])
        result = hpfs_pools(df, 'bearish')
        assert len(result) == 0

    def test_no_ltc_returns_empty(self):
        # Monotone descending closes — no OB bearish LTC (close never > prior high)
        df = make_ohlcv([
            {'open': 105, 'high': 106, 'low': 104, 'close': 104},
            {'open': 104, 'high': 105, 'low': 103, 'close': 103},
            {'open': 103, 'high': 104, 'low': 102, 'close': 102},
        ])
        result = hpfs_pools(df, 'bearish', ltc_type='ob')
        assert len(result) == 0


# ── find_raid_bar ─────────────────────────────────────────────────────────────

class TestFindRaidBar:

    def _df(self):
        return make_ohlcv([
            {'open': 100, 'high': 105, 'low': 98, 'close': 102},   # 2024-01-01
            {'open': 102, 'high': 108, 'low': 100, 'close': 107},  # 2024-01-02 — raids 106
            {'open': 107, 'high': 109, 'low': 105, 'close': 106},  # 2024-01-03
        ])

    def test_bullish_raid_found(self):
        df = self._df()
        ts = find_raid_bar(106.0, 'bullish', df, from_ts=df.index[0])
        assert ts == df.index[1]

    def test_bullish_raid_not_found(self):
        df = self._df()
        ts = find_raid_bar(200.0, 'bullish', df, from_ts=df.index[0])
        assert ts is None

    def test_bearish_raid_found(self):
        df = make_ohlcv([
            {'open': 100, 'high': 102, 'low': 98,  'close': 99},
            {'open': 99,  'high': 101, 'low': 94,  'close': 95},   # low(94) < 97 → raids
            {'open': 95,  'high': 97,  'low': 93,  'close': 94},
        ])
        ts = find_raid_bar(97.0, 'bearish', df, from_ts=df.index[0])
        assert ts == df.index[1]

    def test_respects_from_ts(self):
        df = self._df()
        # from_ts=index[1]: bar 1 is excluded (strictly after), bar 2 high=109 > 106 → found
        ts = find_raid_bar(106.0, 'bullish', df, from_ts=df.index[1])
        assert ts == df.index[2]
        # from_ts=index[2]: nothing after bar 2 → None
        ts_none = find_raid_bar(106.0, 'bullish', df, from_ts=df.index[2])
        assert ts_none is None
