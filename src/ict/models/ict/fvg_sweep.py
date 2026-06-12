"""
FVG Sweep Model  —  ICT 2022 Model
==================================

This is the formal implementation of ICT's 2022 mentorship model — the canonical
``context -> sweep -> MSS w/ displacement -> retrace into FVG -> deliver to draw``
entry sequence. See ``knowledge/ict/models/model-2022.md`` and
``knowledge/ict/entries/entry-sequence.md``.

Checklist (bearish — inverted for bullish):
  1. **Daily bias** from the daily chart: order flow + draw-on-liquidity +
     premium/discount must all agree (else neutral → no trade).
  2. **Mark session liquidity** — the pool set: PDH/PDL, the midnight opening
     range, session swing highs/lows and relative-equal highs/lows.
  3. **Sweep** — a buy-side pool above (bearish) is raided inside the London or
     NY killzone — the Judas move against bias.
  4. **MSS with displacement** on the 3m chart in the bias direction; the
     displacement candle must leave a Fair Value Gap.
  5. **Entry**: limit in that FVG on the retrace. **Stop**: beyond the swept
     extreme. **Target**: opposing liquidity, with a minimum 1:3 R:R floor
     (fall back to a fixed 3R target when the nearest opposing pool is closer
     than 3R).

Source: ICT 2022 mentorship model. Rules: knowledge/ict/models/model-2022.md
"""

import pandas as pd
from dataclasses import dataclass
from typing import Optional

from ict.registry import concept
from ict.concepts.market_structure import SwingPointScanner
from ict.concepts.fair_value_gap import find_fvgs, FVG


@dataclass
class FVGSweepSnapshot:
    """
    Data container for the FVGSweepModel.

    Attributes:
        df_3m:        3-minute bars for the session (entry timeframe)
        df_15m:       15-minute bars covering recent history (pool detection)
        df_daily:     Daily bars for bias determination (pre-session)
        session_date: The calendar date being analyzed (tz-naive, local date)
    """
    df_3m: pd.DataFrame
    df_15m: pd.DataFrame
    df_daily: pd.DataFrame
    session_date: pd.Timestamp


@concept("model-2022")
class FVGSweepModel:
    """
    ICT 2022 Model — Fair Value Gap + Liquidity Sweep intraday model.

    Config keys:
        eq_tolerance_pts      float  Points within which swing highs/lows form an equal pair (default 5)
        swing_lookback        int    Candles each side for a 3-bar swing (default 1)
        killzones             list   [(start,end), ...] NY-local 'HH:MM' windows the sweep may occur in
        daily_lookback        int    Recent daily bars for the order-flow vote (default 5)
        dealing_range_days    int    Daily bars defining the premium/discount dealing range (default 20)
        reh_lookback_days     int    Days back to scan for 15m relative-equal pools (default 5)
        opening_range_minutes int    Minutes after NY midnight defining the opening range (default 30)
        max_bars_sweep_to_mss int    Cap on 3m bars between sweep and MSS (default 30)
        target_min_rr         float  Minimum (and fallback fixed) reward:risk for the target (default 3.0)
    """

    DEFAULT_CONFIG = {
        'eq_tolerance_pts': 5.0,
        'swing_lookback': 1,
        # London KZ (02:00–05:00 NY) and NY AM KZ (07:00–10:00 NY)
        'killzones': [('02:00', '05:00'), ('07:00', '10:00')],
        'daily_lookback': 5,
        'dealing_range_days': 20,
        'reh_lookback_days': 5,
        'opening_range_minutes': 30,
        'max_bars_sweep_to_mss': 30,
        'target_min_rr': 3.0,
    }

    def __init__(self, config: Optional[dict] = None):
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.checks: list = []

    def _log(self, msg: str):
        self.checks.append(msg)

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

    @staticmethod
    def _ny_index(df: pd.DataFrame) -> pd.DatetimeIndex:
        """Return df.index converted to America/New_York (assume UTC if tz-naive)."""
        idx = df.index
        if idx.tz is None:
            idx = idx.tz_localize('UTC')
        return idx.tz_convert('America/New_York')

    # ------------------------------------------------------------------
    # Step 1: Daily bias — order flow + draw + premium/discount
    # ------------------------------------------------------------------

    def _daily_bias(self, daily_df: pd.DataFrame) -> str:
        """
        ICT daily bias from the daily chart. Bullish requires ALL THREE signals
        bullish; bearish requires all three bearish; otherwise neutral.

          1. Order flow  — net delivery of recent daily candles (close drift +
             majority of up/down closes).
          2. Draw        — which untaken daily swing pool (high above / low below)
             is the nearer magnet to current price.
          3. Premium/discount — is price in the discount (favors long) or premium
             (favors short) half of the recent dealing range.
        """
        n = self.config['daily_lookback']
        if daily_df is None or len(daily_df) < max(n, 3):
            self._log("Daily bias: insufficient data → neutral")
            return 'neutral'

        order_flow = self._daily_order_flow(daily_df, n)
        draw = self._daily_draw(daily_df)
        prem_disc = self._daily_premium_discount(daily_df)

        if order_flow == draw == prem_disc == 'bullish':
            self._log("Daily bias: BULLISH (order flow + draw + discount aligned)")
            return 'bullish'
        if order_flow == draw == prem_disc == 'bearish':
            self._log("Daily bias: BEARISH (order flow + draw + premium aligned)")
            return 'bearish'

        self._log(
            f"Daily bias: neutral (order_flow={order_flow}, draw={draw}, "
            f"premium_discount={prem_disc})"
        )
        return 'neutral'

    def _daily_order_flow(self, daily_df: pd.DataFrame, n: int) -> str:
        recent = daily_df.tail(n).dropna(subset=['open', 'close'])
        if len(recent) < 2:
            return 'neutral'
        net = recent['close'].iloc[-1] - recent['close'].iloc[0]
        up = int((recent['close'] > recent['open']).sum())
        down = int((recent['close'] < recent['open']).sum())
        if net > 0 and up >= down:
            return 'bullish'
        if net < 0 and down >= up:
            return 'bearish'
        return 'neutral'

    def _daily_draw(self, daily_df: pd.DataFrame) -> str:
        window = daily_df.tail(self.config['dealing_range_days'])
        scanner = SwingPointScanner(window, lookback=self.config['swing_lookback'])
        scanner.identify_swings()
        last_close = float(daily_df['close'].iloc[-1])

        highs = scanner.swing_highs['swing_high_price'].dropna() if scanner.swing_highs is not None else pd.Series(dtype=float)
        lows = scanner.swing_lows['swing_low_price'].dropna() if scanner.swing_lows is not None else pd.Series(dtype=float)

        highs_above = highs[highs > last_close]
        lows_below = lows[lows < last_close]
        nearest_high = float(highs_above.min()) if len(highs_above) else None
        nearest_low = float(lows_below.max()) if len(lows_below) else None

        if nearest_high is not None and nearest_low is not None:
            dist_up = nearest_high - last_close
            dist_down = last_close - nearest_low
            return 'bullish' if dist_up <= dist_down else 'bearish'
        if nearest_high is not None:
            return 'bullish'
        if nearest_low is not None:
            return 'bearish'
        return 'neutral'

    def _daily_premium_discount(self, daily_df: pd.DataFrame) -> str:
        window = daily_df.tail(self.config['dealing_range_days'])
        rng_hi = float(window['high'].max())
        rng_lo = float(window['low'].min())
        if rng_hi <= rng_lo:
            return 'neutral'
        mid = (rng_hi + rng_lo) / 2
        last_close = float(daily_df['close'].iloc[-1])
        # Discount (below mid) favors longs; premium (above mid) favors shorts.
        return 'bullish' if last_close < mid else 'bearish'

    # ------------------------------------------------------------------
    # Step 2: Build the session-liquidity pool set
    # ------------------------------------------------------------------

    def _build_pools(self, snapshot: FVGSweepSnapshot, before: pd.Timestamp) -> dict:
        """
        Assemble the 2022-model pool set, split by side.

        Returns {'highs': [pool, ...], 'lows': [pool, ...]} where each pool is
        {'extreme_price', 'price', 'source'}. 'highs' are buy-side pools above
        (sweep targets when bearish); 'lows' are sell-side pools below.
        """
        highs: list = []
        lows: list = []

        # --- PDH / PDL: the last completed daily bar before the session ---
        daily = snapshot.df_daily
        if daily is not None and len(daily) > 0:
            before_daily = self._localize_like(before, daily.index)
            prior = daily[daily.index < before_daily]
            if len(prior) > 0:
                pdh = float(prior['high'].iloc[-1])
                pdl = float(prior['low'].iloc[-1])
                highs.append({'extreme_price': pdh, 'price': pdh, 'source': 'PDH'})
                lows.append({'extreme_price': pdl, 'price': pdl, 'source': 'PDL'})

        # --- Midnight opening range (00:00 → +opening_range_minutes NY) ---
        orng = self._opening_range(snapshot.df_3m, snapshot.session_date)
        if orng is not None:
            highs.append({'extreme_price': orng['high'], 'price': orng['high'], 'source': 'OR-high'})
            lows.append({'extreme_price': orng['low'], 'price': orng['low'], 'source': 'OR-low'})

        # --- 15m session swing highs/lows + relative-equal clusters ---
        for cl in self._find_rel_equal_levels(snapshot.df_15m, before, 'bearish'):
            cl['source'] = f"REH×{cl['count']}"
            highs.append(cl)
        for cl in self._find_rel_equal_levels(snapshot.df_15m, before, 'bullish'):
            cl['source'] = f"REL×{cl['count']}"
            lows.append(cl)

        self._log(f"Pools: {len(highs)} buy-side / {len(lows)} sell-side")
        return {'highs': highs, 'lows': lows}

    def _opening_range(self, df_3m: pd.DataFrame, session_date: pd.Timestamp) -> Optional[dict]:
        """High/low of the NY midnight opening range on the session date."""
        ny = self._ny_index(df_3m)
        mins = ny.hour * 60 + ny.minute
        on_date = ny.date == session_date.date()
        in_or = on_date & (mins >= 0) & (mins < self.config['opening_range_minutes'])
        bars = df_3m[in_or]
        if len(bars) == 0:
            return None
        return {'high': float(bars['high'].max()), 'low': float(bars['low'].min())}

    def _find_rel_equal_levels(
        self,
        df_15m: pd.DataFrame,
        before: pd.Timestamp,
        direction: str,
    ) -> list:
        """
        Untested 15m swing highs (bearish) or lows (bullish) in the lookback
        window — singletons and equal-clusters alike. A level already swept
        before the session open is dropped (its stops are gone).

        Returns list of {price, extreme_price, timestamps, count}.
        """
        before = self._localize_like(before, df_15m.index)
        lookback_start = before - pd.Timedelta(days=self.config['reh_lookback_days'])
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
            similar = prices[(prices >= price - tol) & (prices <= price + tol)]
            extreme = extreme_fn(similar.values)

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
    # Step 3: Sweep detection (inside a killzone)
    # ------------------------------------------------------------------

    def _detect_sweep(
        self,
        session_df: pd.DataFrame,
        pools: list,
        direction: str,
    ) -> Optional[dict]:
        """First killzone candle that sweeps a buy-side pool (bearish) or
        sell-side pool (bullish), approached from the correct side."""
        for i, (ts, row) in enumerate(session_df.iterrows()):
            prior_bars = session_df.iloc[:i]
            for pool in pools:
                lvl = pool['extreme_price']
                if direction == 'bearish' and row['high'] > lvl:
                    if i == 0 or prior_bars['low'].min() > lvl:
                        continue  # must approach from below
                    self._log(f"Stop hunt: swept {pool.get('source', 'high')} "
                              f"at {lvl:.2f} @ {ts} (high {row['high']:.2f})")
                    return {'sweep_time': ts, 'cluster': pool, 'stop_level': float(row['high'])}
                if direction == 'bullish' and row['low'] < lvl:
                    if i == 0 or prior_bars['high'].max() < lvl:
                        continue  # must approach from above
                    self._log(f"Stop hunt: swept {pool.get('source', 'low')} "
                              f"at {lvl:.2f} @ {ts} (low {row['low']:.2f})")
                    return {'sweep_time': ts, 'cluster': pool, 'stop_level': float(row['low'])}
        return None

    # ------------------------------------------------------------------
    # Step 4: Market structure shift (MSS) on 3m after the sweep
    # ------------------------------------------------------------------

    def _detect_bms(
        self,
        df_3m: pd.DataFrame,
        direction: str,
        after_time: pd.Timestamp,
    ) -> Optional[dict]:
        """First 3m swing low (bearish) / high (bullish) after the sweep that
        gets closed through — capped at max_bars_sweep_to_mss bars."""
        after_time = self._localize_like(after_time, df_3m.index)
        df_after = df_3m[df_3m.index > after_time].copy()
        df_after = df_after.iloc[: self.config['max_bars_sweep_to_mss']]
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
                        f"MSS: closed {'below' if direction == 'bearish' else 'above'} "
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
    # Step 5: FVG from the displacement candle
    # ------------------------------------------------------------------

    def _find_entry_fvg(self, bms_result: dict, direction: str) -> Optional[FVG]:
        """FVG created by the displacement around the MSS candle."""
        df_after = bms_result['df_after']
        pos = bms_result['bms_pos']
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
    # Step 6: Target — opposing liquidity with a 3R floor/fallback
    # ------------------------------------------------------------------

    def _find_target(
        self,
        direction: str,
        entry: float,
        stop: float,
        target_pools: list,
    ) -> float:
        """
        Target the nearest opposing-liquidity pool beyond entry, provided it pays
        at least target_min_rr. When the nearest pool is closer than that floor
        (or there is none), fall back to a fixed target_min_rr:1 target.
        """
        risk = abs(stop - entry)
        min_rr = self.config['target_min_rr']
        floor = (entry - min_rr * risk) if direction == 'short' else (entry + min_rr * risk)

        if direction == 'short':
            candidates = [p['extreme_price'] for p in target_pools if p['extreme_price'] < entry]
            pool = max(candidates) if candidates else None  # nearest below
        else:
            candidates = [p['extreme_price'] for p in target_pools if p['extreme_price'] > entry]
            pool = min(candidates) if candidates else None  # nearest above

        if pool is not None and risk > 0:
            pool_rr = abs(entry - pool) / risk
            if pool_rr >= min_rr:
                self._log(f"Target: opposing pool {pool:.2f}  R:R={pool_rr:.2f}")
                return float(pool)
            self._log(f"Target: nearest pool {pool:.2f} only {pool_rr:.2f}R "
                      f"< {min_rr} → fixed {min_rr}R floor {floor:.2f}")
            return float(floor)

        self._log(f"Target: no opposing pool → fixed {min_rr}R floor {floor:.2f}")
        return float(floor)

    # ------------------------------------------------------------------
    # Killzone session window filter
    # ------------------------------------------------------------------

    def _session_mask(self, df: pd.DataFrame, session_date: pd.Timestamp) -> pd.Series:
        """True for bars on session_date that fall inside ANY configured killzone
        (NY-local). DST handled via America/New_York."""
        ny = self._ny_index(df)
        ny_min = ny.hour * 60 + ny.minute
        on_date = ny.date == session_date.date()
        in_any = pd.Series(False, index=df.index)
        for start, end in self.config['killzones']:
            sh, sm = map(int, start.split(':'))
            eh, em = map(int, end.split(':'))
            window = (ny_min >= sh * 60 + sm) & (ny_min < eh * 60 + em)
            in_any = in_any | pd.Series(on_date & window, index=df.index)
        return in_any

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_signal(self, snapshot: FVGSweepSnapshot) -> dict:
        """Evaluate one session for a valid 2022-model setup."""
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

        # 1. Daily bias
        bias = self._daily_bias(snapshot.df_daily)
        if bias == 'neutral':
            self._log("Rule of exclusion: no daily bias → no trade")
            return base
        direction = 'short' if bias == 'bearish' else 'long'

        # 2. Pool set (built from data before the session open)
        before = pd.Timestamp(snapshot.session_date.date())
        pools = self._build_pools(snapshot, before)
        entry_pools = pools['highs'] if bias == 'bearish' else pools['lows']
        target_pools = pools['lows'] if bias == 'bearish' else pools['highs']
        if not entry_pools:
            self._log(f"Rule of exclusion: no {'buy' if bias == 'bearish' else 'sell'}-side pools to sweep")
            return base

        # 3. Filter 3m data to the killzone windows on session_date
        session_df = snapshot.df_3m[self._session_mask(snapshot.df_3m, snapshot.session_date)]
        if len(session_df) < 5:
            self._log("Rule of exclusion: insufficient killzone data")
            return base

        # 4. Sweep
        sweep = self._detect_sweep(session_df, entry_pools, bias)
        if sweep is None:
            self._log("Rule of exclusion: no stop hunt in killzone")
            return base

        # 5. MSS on 3m after sweep
        bms = self._detect_bms(snapshot.df_3m, bias, sweep['sweep_time'])
        if bms is None:
            self._log("Rule of exclusion: no MSS after stop hunt")
            return base

        # 6. FVG from displacement
        fvg = self._find_entry_fvg(bms, bias)
        if fvg is None:
            self._log("Rule of exclusion: no FVG at MSS displacement")
            return base

        # 7. Stop at swept extreme — geometry sanity
        stop = sweep['cluster']['extreme_price']
        if direction == 'short' and stop <= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not above entry {fvg.entry:.2f}")
            return base
        if direction == 'long' and stop >= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not below entry {fvg.entry:.2f}")
            return base

        # 8. Target — opposing liquidity, 3R floor
        target = self._find_target(direction, entry=fvg.entry, stop=stop, target_pools=target_pools)

        # Session midpoint (chart context only)
        pre_sweep = session_df[session_df.index <= sweep['sweep_time']]
        ref = pre_sweep if len(pre_sweep) > 0 else session_df
        midpoint = (float(ref['high'].max()) + float(ref['low'].min())) / 2

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
            'swept_pool': sweep['cluster'].get('source'),
            'bms_time': bms['bms_time'],
            'bms_swing_level': bms['bms_swing_level'],
            'session_midpoint': midpoint,
            'checks': self.checks,
        }
