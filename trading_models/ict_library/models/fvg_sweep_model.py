"""
FVG Sweep Model
===============

ICT intraday setup: liquidity sweep + break of market structure + fair value gap entry.

Checklist (bearish — inverted for bullish):
  1. Weekly bias is bearish
  2. Relative equal highs identified on 15m (buy stops resting above)
  3. Price sweeps above those highs during NY session window
  4. Break of 3-bar market structure on 2m after the sweep
  5. Fair Value Gap left by the displacement candle
  6. Enter short at limit (top of FVG)
  7. Stop at the high of the swept swing high
  8. Target: nearest swing low below the 50% of session range

Source: ICT — "Elements of a Trade Setup"
Rules: trading_models/strategies/notes/ict-elements-of-a-trade-setup.md
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional

from ict_library.core.market_structure import SwingPointScanner
from ict_library.core.fair_value_gap import find_fvgs, FVG


@dataclass
class FVGSweepSnapshot:
    """
    Data container for the FVGSweepModel.

    Attributes:
        df_2m:       2-minute bars for the session (entry timeframe)
        df_15m:      15-minute bars covering recent history (swing/REH detection)
        df_weekly:   Weekly bars for bias determination
        session_date: The calendar date being analyzed (tz-naive, local date)
    """
    df_2m: pd.DataFrame
    df_15m: pd.DataFrame
    df_weekly: pd.DataFrame
    session_date: pd.Timestamp


class FVGSweepModel:
    """
    ICT Fair Value Gap + Liquidity Sweep intraday model.

    Config keys:
        eq_tolerance_pts  float  Point tolerance to pair two swing highs/lows as equal (default 5)
        swing_lookback    int    Candles each side for 3-bar swing (default 1)
        session_start_ny  str    NY session open time 'HH:MM' (default '08:30')
        session_end_ny    str    NY session end time 'HH:MM' (default '11:00')
        weekly_lookback   int    Recent weekly bars for bias vote (default 4)
    """

    DEFAULT_CONFIG = {
        'eq_tolerance_pts': 5.0,   # points within which two swing highs/lows form an equal pair
        'swing_lookback': 1,
        'session_start_ny': '09:30',
        'session_end_ny': '11:00',
        'weekly_lookback': 4,
        'reh_lookback_days': 5,
        'target_rr': 1.5,          # fixed reward:risk ratio for target placement
    }

    def __init__(self, config: Optional[dict] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.checks: list = []

    def _log(self, msg: str):
        self.checks.append(msg)

    # ------------------------------------------------------------------
    # Step 1: Weekly bias
    # ------------------------------------------------------------------

    def _weekly_bias(self, weekly_df: pd.DataFrame) -> str:
        n = self.config['weekly_lookback']
        if len(weekly_df) < n:
            self._log("Weekly bias: insufficient data → neutral")
            return 'neutral'
        recent = weekly_df.tail(n).dropna(subset=['open', 'close'])
        bearish = (recent['close'] < recent['open']).sum()
        bullish = (recent['close'] >= recent['open']).sum()
        threshold = max(2, int(n * 0.6))
        if bearish >= threshold:
            self._log(f"Weekly bias: bearish ({bearish}/{n} bars)")
            return 'bearish'
        if bullish >= threshold:
            self._log(f"Weekly bias: bullish ({bullish}/{n} bars)")
            return 'bullish'
        self._log(f"Weekly bias: neutral (bearish={bearish}, bullish={bullish})")
        return 'neutral'

    # ------------------------------------------------------------------
    # Step 2: Relative equal highs / lows
    # ------------------------------------------------------------------

    def _find_rel_equal_levels(
        self,
        df_15m: pd.DataFrame,
        before: pd.Timestamp,
        direction: str,
    ) -> list:
        """
        Find untested 15m swing highs (bearish) or swing lows (bullish) in the
        lookback window.

        A valid level is:
          - A single 15m swing high/low, OR
          - Two or more within eq_tolerance_pts of each other (equal highs/lows)

        A level is skipped if it was already taken (swept) by a subsequent bar
        before the session open — meaning the buy/sell stops are no longer resting there.

        Returns list of dicts: {price, extreme_price, timestamps, count}
          - price: mean of the cluster (or the single price)
          - extreme_price: highest high (bearish) or lowest low (bullish) — sweep trigger
        """
        lookback_start = before - pd.Timedelta(days=self.config['reh_lookback_days'])
        lookback_start = self._localize_like(lookback_start, df_15m.index)
        df = df_15m[(df_15m.index >= lookback_start) & (df_15m.index < before)].copy()
        if len(df) < 3:
            return []

        scanner = SwingPointScanner(df, lookback=self.config['swing_lookback'])
        scanner.identify_swings()

        tol = self.config['eq_tolerance_pts']

        if direction == 'bearish':
            if scanner.swing_highs is None or len(scanner.swing_highs) == 0:
                return []
            prices = scanner.swing_highs['swing_high_price'].dropna()
            extreme_fn = max
            def was_taken(extreme_price, df_after):
                return len(df_after) > 0 and df_after['high'].max() > extreme_price
        else:
            if scanner.swing_lows is None or len(scanner.swing_lows) == 0:
                return []
            prices = scanner.swing_lows['swing_low_price'].dropna()
            extreme_fn = min
            def was_taken(extreme_price, df_after):
                return len(df_after) > 0 and df_after['low'].min() < extreme_price

        clusters = []
        used = set()
        for i, (ts, price) in enumerate(prices.items()):
            if i in used:
                continue
            # Group this swing with any other within tolerance
            similar = prices[(prices >= price - tol) & (prices <= price + tol)]
            extreme = extreme_fn(similar.values)

            # Skip if the level was already swept before the session open
            last_ts = max(similar.index)
            df_after_cluster = df[df.index > last_ts]
            if was_taken(extreme, df_after_cluster):
                for j, idx in enumerate(prices.index):
                    if idx in similar.index:
                        used.add(j)
                continue

            clusters.append({
                'price': float(similar.mean()),
                'extreme_price': float(extreme),
                'timestamps': similar.index.tolist(),
                'count': int(len(similar)),
            })
            for j, idx in enumerate(prices.index):
                if idx in similar.index:
                    used.add(j)

        return clusters

    # ------------------------------------------------------------------
    # Step 3: Stop hunt / sweep detection
    # ------------------------------------------------------------------

    def _detect_sweep(
        self,
        session_df: pd.DataFrame,
        clusters: list,
        direction: str,
    ) -> Optional[dict]:
        """
        Returns the first candle that sweeps above (bearish) or below (bullish)
        a relative equal level.
        """
        bars = list(session_df.iterrows())
        for i, (ts, row) in enumerate(bars):
            prior_bars = session_df.iloc[:i]
            for cluster in clusters:
                if direction == 'bearish' and row['high'] > cluster['extreme_price']:
                    # Require at least one prior session bar was at or below the REH
                    # (price must approach from below — not just open above it)
                    if i == 0 or prior_bars['low'].min() > cluster['extreme_price']:
                        continue
                    self._log(
                        f"Stop hunt: swept REH at {cluster['extreme_price']:.2f} "
                        f"@ {ts} (sweep candle high {row['high']:.2f})"
                    )
                    return {
                        'sweep_time': ts,
                        'sweep_candle_high': float(row['high']),
                        'cluster': cluster,
                        'stop_level': float(row['high']),
                    }
                if direction == 'bullish' and row['low'] < cluster['extreme_price']:
                    # Require at least one prior session bar was at or above the REL
                    if i == 0 or prior_bars['high'].max() < cluster['extreme_price']:
                        continue
                    self._log(
                        f"Stop hunt: swept REL at {cluster['extreme_price']:.2f} "
                        f"@ {ts} (sweep candle low {row['low']:.2f})"
                    )
                    return {
                        'sweep_time': ts,
                        'sweep_candle_low': float(row['low']),
                        'cluster': cluster,
                        'stop_level': float(row['low']),
                    }
        return None

    # ------------------------------------------------------------------
    # Step 4: Break of market structure
    # ------------------------------------------------------------------

    def _detect_bms(
        self,
        df_2m: pd.DataFrame,
        direction: str,
        after_time: pd.Timestamp,
    ) -> Optional[dict]:
        """
        After the sweep, find the first 3-bar swing low (bearish) that then
        gets closed through — that's the BMS.

        Returns dict with bms_time, bms_swing_level, df_after, bms_pos.
        """
        after_time = self._localize_like(after_time, df_2m.index)
        df_after = df_2m[df_2m.index > after_time].copy()
        if len(df_after) < 5:
            return None

        scanner = SwingPointScanner(df_after, lookback=self.config['swing_lookback'])
        scanner.identify_swings()

        if direction == 'bearish':
            swings = scanner.swing_lows
            price_col = 'swing_low_price'
            def broke(row, level): return row['close'] < level
        else:
            swings = scanner.swing_highs
            price_col = 'swing_high_price'
            def broke(row, level): return row['close'] > level

        if swings is None or len(swings) == 0:
            return None

        for swing_ts, swing_row in swings.iterrows():
            level = swing_row[price_col]
            after_swing = df_after[df_after.index > swing_ts]
            for bms_ts, bms_row in after_swing.iterrows():
                if broke(bms_row, level):
                    bms_pos = df_after.index.get_loc(bms_ts)
                    self._log(
                        f"BMS: closed {'below' if direction == 'bearish' else 'above'} "
                        f"swing at {level:.2f} @ {bms_ts}"
                    )
                    return {
                        'bms_time': bms_ts,
                        'bms_swing_level': float(level),
                        'bms_pos': bms_pos,
                        'df_after': df_after,
                    }
        return None

    # ------------------------------------------------------------------
    # Step 5: FVG from displacement candle
    # ------------------------------------------------------------------

    def _find_entry_fvg(self, bms_result: dict, direction: str) -> Optional[FVG]:
        """
        Look for a FVG created by the displacement candle at/around the BMS.
        Returns the first FVG found at or just before the BMS candle.
        """
        df_after = bms_result['df_after']
        pos = bms_result['bms_pos']

        # Search window: 2 candles before BMS through 2 after (need i+1 to exist)
        start = max(0, pos - 2)
        end = min(len(df_after), pos + 3)
        search_df = df_after.iloc[start:end]

        if len(search_df) < 3:
            return None

        fvgs = find_fvgs(search_df, direction=direction)
        if fvgs:
            self._log(
                f"FVG: {direction} gap {fvgs[0].bottom:.2f}–{fvgs[0].top:.2f} "
                f"@ {fvgs[0].timestamp}, entry limit {fvgs[0].entry:.2f}"
            )
            return fvgs[0]
        return None

    # ------------------------------------------------------------------
    # Step 6: Target — fixed 1.5:1 R:R from entry
    # ------------------------------------------------------------------

    def _find_target(
        self,
        direction: str,
        entry: float,
        stop: float,
    ) -> float:
        risk = abs(stop - entry)
        reward = risk * self.config['target_rr']
        target = (entry - reward) if direction == 'bearish' else (entry + reward)
        self._log(
            f"Target: {target:.2f}  risk={risk:.1f}pts  "
            f"reward={reward:.1f}pts  R:R={self.config['target_rr']}"
        )
        return target

    # ------------------------------------------------------------------
    # Timezone helpers
    # ------------------------------------------------------------------

    def _localize_like(self, ts: pd.Timestamp, ref: pd.DatetimeIndex) -> pd.Timestamp:
        """Make ts tz-aware/naive to match ref index."""
        if ref.tz is not None and ts.tz is None:
            return ts.tz_localize(ref.tz)
        if ref.tz is None and ts.tz is not None:
            return ts.replace(tzinfo=None)
        return ts

    # ------------------------------------------------------------------
    # Session window filter
    # ------------------------------------------------------------------

    def _session_mask(self, df: pd.DataFrame, session_date: pd.Timestamp) -> pd.Series:
        """Filter to NY session window on a specific date. Handles DST via America/New_York tz."""
        idx = df.index
        if idx.tz is None:
            idx = idx.tz_localize('UTC')
        ny = idx.tz_convert('America/New_York')
        sh, sm = map(int, self.config['session_start_ny'].split(':'))
        eh, em = map(int, self.config['session_end_ny'].split(':'))
        start_min = sh * 60 + sm
        end_min = eh * 60 + em
        ny_min = ny.hour * 60 + ny.minute
        ny_date = ny.date
        target_date = session_date.date()
        return pd.Series(
            (ny_date == target_date) & (ny_min >= start_min) & (ny_min < end_min),
            index=df.index,
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_signal(self, snapshot: FVGSweepSnapshot) -> dict:
        """
        Evaluate a single session for a valid FVG sweep setup.

        Returns dict:
            actionable      bool
            direction       'long' | 'short' | None
            entry           float | None   limit price (top/bottom of FVG)
            entry_time      Timestamp | None
            stop            float | None   at swept swing high/low
            target          float | None
            fvg_top         float | None
            fvg_bottom      float | None
            sweep_level     float | None
            session_midpoint float | None
            checks          list[str]
        """
        self.checks = []

        base = {
            'actionable': False,
            'direction': None,
            'entry': None,
            'entry_time': None,
            'stop': None,
            'target': None,
            'fvg_top': None,
            'fvg_bottom': None,
            'sweep_level': None,
            'session_midpoint': None,
            'checks': self.checks,
        }

        # 1. Weekly bias
        bias = self._weekly_bias(snapshot.df_weekly)
        if bias == 'neutral':
            self._log("Rule of exclusion: no weekly bias → no trade")
            return base

        direction = 'short' if bias == 'bearish' else 'long'

        # 2. Relative equal levels on 15m (before session open)
        session_open = self._localize_like(
            pd.Timestamp(snapshot.session_date.date()),
            snapshot.df_15m.index,
        )
        clusters = self._find_rel_equal_levels(snapshot.df_15m, session_open, bias)
        if not clusters:
            self._log(f"Rule of exclusion: no relative equal {'highs' if bias == 'bearish' else 'lows'} found")
            return base
        self._log(f"Found {len(clusters)} REH/REL cluster(s)")

        # 3. Filter 2m data to session window on session_date only
        mask = self._session_mask(snapshot.df_2m, snapshot.session_date)
        session_df = snapshot.df_2m[mask]
        if len(session_df) < 5:
            self._log("Rule of exclusion: insufficient session data")
            return base

        # 4. Detect sweep
        sweep = self._detect_sweep(session_df, clusters, bias)
        if sweep is None:
            self._log("Rule of exclusion: no stop hunt detected in session window")
            return base

        # 5. BMS on 2m after sweep
        bms = self._detect_bms(snapshot.df_2m, bias, sweep['sweep_time'])
        if bms is None:
            self._log("Rule of exclusion: no BMS after stop hunt")
            return base

        # 6. FVG from displacement candle
        fvg = self._find_entry_fvg(bms, bias)
        if fvg is None:
            self._log("Rule of exclusion: no FVG at BMS displacement candle")
            return base

        # 7. Stop at the swept REH/REL level
        stop = sweep['cluster']['extreme_price']
        if direction == 'short' and stop <= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not above entry {fvg.entry:.2f} → invalid geometry")
            return base
        if direction == 'long' and stop >= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not below entry {fvg.entry:.2f} → invalid geometry")
            return base

        # 8. Target — fixed 1.5:1 R:R
        target = self._find_target(bias, entry=fvg.entry, stop=stop)

        # Session midpoint for chart context only
        pre_sweep = session_df[session_df.index <= sweep['sweep_time']]
        session_high = float(pre_sweep['high'].max()) if len(pre_sweep) > 0 else float(session_df['high'].max())
        session_low = float(pre_sweep['low'].min()) if len(pre_sweep) > 0 else float(session_df['low'].min())
        midpoint = (session_high + session_low) / 2

        self._log(f"Signal: {direction.upper()} entry={fvg.entry:.2f} stop={stop:.2f} target={target:.2f}")

        return {
            'actionable': True,
            'direction': direction,
            'entry': fvg.entry,
            'entry_time': fvg.timestamp,
            'stop': stop,
            'target': target,
            'fvg_top': fvg.top,
            'fvg_bottom': fvg.bottom,
            'sweep_level': sweep['stop_level'],
            'sweep_time': sweep['sweep_time'],
            'reh_price': float(sweep['cluster']['extreme_price']),
            'bms_time': bms['bms_time'],
            'bms_swing_level': bms['bms_swing_level'],
            'session_midpoint': midpoint,
            'checks': self.checks,
        }
