"""
ICT 2022 Model
==================================

``context -> sweep -> MSS w/ displacement -> retrace into FVG -> deliver to draw``

Checklist (bearish — inverted for bullish):
  1. Daily bias  — order flow + draw + premium/discount must agree.
  2. Pool set    — PDH/PDL, opening range, REH/REL from the 15m chart.
  3. Sweep       — a buy-side pool raided inside a killzone.
  4. MSS         — 3m close through the prior swing with displacement + FVG.
  5. Entry/stop  — limit into FVG; stop beyond swept extreme.
  6. Target      — opposing liquidity, 1:3 R:R floor.

See knowledge/ict/models/model-2022.md
"""

import pandas as pd
from dataclasses import dataclass
from typing import Optional

from ict.registry import concept, params as registry_params
from ict.models.intermediate.daily_bias import daily_bias_components
from ict.concepts.fair_value_gap import find_fvgs, FVG
from ict.concepts.killzones import session_mask
from ict.concepts.liquidity_sweep import first_breach
from ict.concepts.market_structure import detect_mss, find_relative_equal_levels
from ict.concepts.premium_discount import premium_discount
from ict.concepts.sessions import opening_range
from ict.concepts.targets import find_liquidity_target
from ict.utils.time_utils import localize_like


@dataclass
class Model2022Snapshot:
    """
    Attributes:
        df_3m:        3-minute bars for the session (entry timeframe).
        df_15m:       15-minute bars for pool detection.
        df_daily:     Daily bars for bias (pre-session).
        session_date: Calendar date being analyzed (tz-naive local date).
    """
    df_3m: pd.DataFrame
    df_15m: pd.DataFrame
    df_daily: pd.DataFrame
    session_date: pd.Timestamp


@concept("model-2022", depends_on=["daily-bias", "fair-value-gap", "killzones", "liquidity-sweep-stop-hunt", "market-structure-shift", "relative-equal-highs-lows", "sessions-and-ranges", "targets-and-exits"])
class Model2022:
    """
    ICT 2022 Model — FVG + Liquidity Sweep intraday model.

    Config keys:
        eq_tolerance_pts      float  Points for REH/REL cluster tolerance (default 5)
        swing_lookback        int    Bar lookback for SwingPointScanner (default 1)
        killzones             list   [(start,end), ...] NY 'HH:MM' windows for sweep
        daily_lookback        int    Daily bars for order-flow vote (default 5)
        dealing_range_days    int    Daily bars for premium/discount range (default 20)
        reh_lookback_days     int    Days back to scan 15m for equal pools (default 5)
        opening_range_start   str    NY start time for opening range (default '09:30')
        opening_range_minutes int    Minutes after opening_range_start (default 30)
        max_bars_sweep_to_mss int    Cap on 3m bars between sweep and MSS (default 30)
        target_min_rr         float  Minimum R:R; also the fixed fallback (default 3.0)
    """

    # The opening-range window is owned by the sessions-and-ranges concept; its
    # canonical default lives in that concept's frontmatter (see __init__). The
    # values below are only fallbacks if the frontmatter can't be read.
    DEFAULT_CONFIG = {
        'eq_tolerance_pts': 5.0,
        'swing_lookback': 1,
        'killzones': [('02:00', '05:00'), ('07:00', '10:00')],
        'daily_lookback': 5,
        'dealing_range_days': 20,
        'reh_lookback_days': 5,
        'opening_range_start': '09:30',
        'opening_range_minutes': 30,
        'max_bars_sweep_to_mss': 30,
        'target_min_rr': 3.0,
    }

    def __init__(self, config: Optional[dict] = None):
        # Single source of truth for the OR window: the sessions-and-ranges
        # concept frontmatter. Fall back to DEFAULT_CONFIG, then apply caller config.
        defaults = dict(self.DEFAULT_CONFIG)
        or_params = registry_params('sessions-and-ranges')
        if 'opening_range_start' in or_params:
            defaults['opening_range_start'] = str(or_params['opening_range_start'])
        if 'opening_range_minutes' in or_params:
            defaults['opening_range_minutes'] = int(or_params['opening_range_minutes'])
        self.config = {**defaults, **(config or {})}
        self.checks: list = []

    def _log(self, msg: str):
        self.checks.append(msg)

    # ------------------------------------------------------------------
    # Step 1: Daily bias
    # ------------------------------------------------------------------

    def _daily_bias(self, daily_df: pd.DataFrame) -> str:
        components = daily_bias_components(
            daily_df,
            lookback=self.config['daily_lookback'],
            dealing_range_days=self.config['dealing_range_days'],
            swing_lookback=self.config['swing_lookback'],
        )
        bias = components['bias']
        if bias == 'neutral':
            self._log(
                f"Daily bias: neutral (order_flow={components['order_flow']}, "
                f"draw={components['draw']}, "
                f"premium_discount={components['premium_discount']})"
            )
        else:
            self._log(f"Daily bias: {bias.upper()} (order flow + draw + discount aligned)")
        return bias

    # ------------------------------------------------------------------
    # Step 2: Session liquidity pool set
    # ------------------------------------------------------------------

    def _build_pools(self, snapshot: Model2022Snapshot, before: pd.Timestamp) -> dict:
        """PDH/PDL + opening range + REH/REL. Returns {highs: [...], lows: [...]}."""
        highs: list = []
        lows:  list = []

        # PDH / PDL — liquidity going into today; "taken" the first time the new
        # session trades through it, so its formation reference is the midnight
        # NY day boundary (the prior day's own high/low must not self-trigger).
        session_open = pd.Timestamp(f"{snapshot.session_date.date()} 00:00",
                                    tz='America/New_York').tz_convert('UTC')
        daily = snapshot.df_daily
        if daily is not None and len(daily) > 0:
            before_daily = localize_like(before, daily.index)
            prior = daily[daily.index < before_daily]
            if len(prior) > 0:
                pdh = float(prior['high'].iloc[-1])
                pdl = float(prior['low'].iloc[-1])
                pdh_ts = prior.index[-1]
                pdl_ts = prior.index[-1]
                highs.append({'extreme_price': pdh, 'price': pdh, 'source': 'PDH',
                              'timestamps': [pdh_ts], 'formed_at': session_open})
                lows.append({'extreme_price': pdl, 'price': pdl, 'source': 'PDL',
                             'timestamps': [pdl_ts], 'formed_at': session_open})

        # Opening range (09:30–10:00 NY RTH open by default)
        orng = opening_range(
            snapshot.df_3m, snapshot.session_date,
            minutes=self.config['opening_range_minutes'],
            start_ny=self.config['opening_range_start'],
        )
        if orng is not None:
            # The OR is only known once the range closes — sweeps before
            # range_end would be look-ahead, so it can't be raided in-window.
            highs.append({'extreme_price': orng['high'], 'price': orng['high'], 'source': 'OR-high',
                          'timestamps': [orng['high_time']], 'formed_at': orng['range_end'],
                          'range_start': orng['range_start'], 'range_end': orng['range_end'],
                          'range_low': orng['low']})
            lows.append({'extreme_price': orng['low'],  'price': orng['low'],  'source': 'OR-low',
                         'timestamps': [orng['low_time']], 'formed_at': orng['range_end'],
                         'range_start': orng['range_start'], 'range_end': orng['range_end'],
                         'range_high': orng['high']})

        # 15m relative-equal highs / lows
        for cl in find_relative_equal_levels(
            snapshot.df_15m, before, 'highs',
            lookback_days=self.config['reh_lookback_days'],
            tolerance_pts=self.config['eq_tolerance_pts'],
            swing_lookback=self.config['swing_lookback'],
        ):
            cl['source'] = f"REH×{cl['count']}"
            cl['formed_at'] = max(cl['timestamps']) if cl.get('timestamps') else None
            highs.append(cl)

        for cl in find_relative_equal_levels(
            snapshot.df_15m, before, 'lows',
            lookback_days=self.config['reh_lookback_days'],
            tolerance_pts=self.config['eq_tolerance_pts'],
            swing_lookback=self.config['swing_lookback'],
        ):
            cl['source'] = f"REL×{cl['count']}"
            cl['formed_at'] = max(cl['timestamps']) if cl.get('timestamps') else None
            lows.append(cl)

        self._log(f"Pools: {len(highs)} buy-side / {len(lows)} sell-side")
        return {'highs': highs, 'lows': lows}

    # ------------------------------------------------------------------
    # Step 3: Sweep (inside a killzone)
    # ------------------------------------------------------------------

    def _detect_sweep(
        self,
        df_3m: pd.DataFrame,
        kz_mask: pd.Series,
        pools: list,
        direction: str,
    ) -> Optional[dict]:
        """
        Find the earliest valid stop hunt.

        A pool is only a valid sweep target if its liquidity is still resting:
        the FIRST time price trades through it since it formed must land inside a
        killzone. If the level was first taken earlier — outside a killzone or on
        a prior session — the pool is dead (already mitigated) and is skipped.
        See ict.concepts.liquidity_sweep.first_breach.
        """
        side = 'high' if direction == 'bearish' else 'low'
        kz_times = set(df_3m.index[kz_mask.to_numpy()])

        best = None
        for pool in pools:
            lvl = pool['extreme_price']
            ts, row = first_breach(df_3m, lvl, side, after=pool.get('formed_at'))
            if ts is None or ts not in kz_times:
                continue  # never taken, or first taken outside a killzone → dead
            if best is None or ts < best['sweep_time']:
                stop_level = float(row['high'] if side == 'high' else row['low'])
                best = {'sweep_time': ts, 'cluster': pool, 'stop_level': stop_level}

        if best is not None:
            c = best['cluster']
            self._log(
                f"Stop hunt: swept {c.get('source', side)} at "
                f"{c['extreme_price']:.2f} @ {best['sweep_time']} "
                f"(first raid since formation)"
            )
        return best

    # ------------------------------------------------------------------
    # Step 4: MSS with displacement on 3m
    # ------------------------------------------------------------------

    def _detect_bms(
        self,
        df_3m: pd.DataFrame,
        direction: str,
        after_time: pd.Timestamp,
    ) -> Optional[dict]:
        """Thin wrapper around detect_mss; adds df_after slice for FVG search."""
        after_time = localize_like(after_time, df_3m.index)
        result = detect_mss(
            df_3m,
            direction=direction,
            swing_lookback=self.config['swing_lookback'],
            max_bars_after_sweep=self.config['max_bars_sweep_to_mss'],
            sweep_time=after_time,
        )
        if result is None:
            return None

        cutoff = df_3m.index.get_indexer([after_time], method='nearest')[0]
        end     = min(cutoff + self.config['max_bars_sweep_to_mss'] + 1, len(df_3m))
        df_after = df_3m.iloc[cutoff:end]
        bms_pos  = int(df_after.index.get_indexer([result['break_time']], method='nearest')[0])

        self._log(
            f"MSS: closed {'below' if direction == 'bearish' else 'above'} "
            f"swing at {result['broken_level']:.2f} @ {result['break_time']}"
        )
        return {
            'bms_time':       result['break_time'],
            'bms_swing_level': result['broken_level'],
            'bms_pos':        bms_pos,
            'df_after':       df_after,
        }

    # ------------------------------------------------------------------
    # Step 5: FVG from the displacement candle
    # ------------------------------------------------------------------

    def _find_entry_fvg(self, bms_result: dict, direction: str) -> Optional[FVG]:
        df_after = bms_result['df_after']
        pos      = bms_result['bms_pos']
        search   = df_after.iloc[max(0, pos - 2): min(len(df_after), pos + 3)]
        if len(search) < 3:
            return None
        fvgs = find_fvgs(search, direction=direction)
        if fvgs:
            f = fvgs[0]
            self._log(f"FVG: {direction} gap {f.bottom:.2f}–{f.top:.2f} @ {f.timestamp}, entry {f.entry:.2f}")
            return f
        return None

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def generate_signal(self, snapshot: Model2022Snapshot) -> dict:
        """Evaluate one session for a valid 2022-model setup."""
        self.checks = []
        base = {
            'actionable': False, 'direction': None,
            'entry': None, 'entry_time': None,
            'stop': None, 'target': None,
            'fvg_top': None, 'fvg_bottom': None,
            'sweep_level': None, 'session_midpoint': None,
            'checks': self.checks,
        }

        # 1. Daily bias
        bias = self._daily_bias(snapshot.df_daily)
        if bias == 'neutral':
            self._log("Rule of exclusion: no daily bias → no trade")
            return base
        direction = 'short' if bias == 'bearish' else 'long'

        # 1b. Premium/discount entry zone (soft check — log misalignment)
        # Bearish bias should enter from premium; bullish from discount.
        pd_signal = premium_discount(snapshot.df_daily, self.config['dealing_range_days'])
        pd_aligned = (bias == 'bearish' and pd_signal == 'bearish') or \
                     (bias == 'bullish' and pd_signal == 'bullish')
        self._log(f"P/D zone: {pd_signal} ({'aligned' if pd_aligned else 'misaligned with bias'})")

        # 2. Pool set
        before = pd.Timestamp(snapshot.session_date.date())
        pools  = self._build_pools(snapshot, before)
        entry_pools  = pools['highs'] if bias == 'bearish' else pools['lows']
        target_pools = pools['lows']  if bias == 'bearish' else pools['highs']
        if not entry_pools:
            self._log(f"Rule of exclusion: no {'buy' if bias == 'bearish' else 'sell'}-side pools")
            return base

        # 3. Killzone filter + sweep
        kz_mask = session_mask(snapshot.df_3m, snapshot.session_date, self.config['killzones'])
        if int(kz_mask.sum()) < 5:
            self._log("Rule of exclusion: insufficient killzone data")
            return base
        sweep = self._detect_sweep(snapshot.df_3m, kz_mask, entry_pools, bias)
        if sweep is None:
            self._log("Rule of exclusion: no stop hunt in killzone")
            return base

        # 4. MSS
        bms = self._detect_bms(snapshot.df_3m, bias, sweep['sweep_time'])
        if bms is None:
            self._log("Rule of exclusion: no MSS after stop hunt")
            return base

        # 5. FVG
        fvg = self._find_entry_fvg(bms, bias)
        if fvg is None:
            self._log("Rule of exclusion: no FVG at MSS displacement")
            return base

        # 6. Stop geometry check — stop beyond the swept extreme (the wick that
        #    raided the pool), NOT the pool level itself. Price already traded
        #    through the pool, so the pool is not a valid invalidation point;
        #    using it produces near-zero-risk stops that get clipped instantly.
        stop = sweep['stop_level']
        if direction == 'short' and stop <= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not above entry {fvg.entry:.2f}")
            return base
        if direction == 'long' and stop >= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not below entry {fvg.entry:.2f}")
            return base

        # 7. Target
        target = find_liquidity_target(
            direction, entry=fvg.entry, stop=stop,
            target_pools=target_pools, min_rr=self.config['target_min_rr'],
        )
        rr = abs(target - fvg.entry) / abs(stop - fvg.entry) if stop != fvg.entry else 0
        self._log(f"Target: {target:.2f}  R:R={rr:.2f}")

        # Session midpoint (chart context) — over the killzone bars up to the sweep
        kz_bars = snapshot.df_3m[kz_mask.to_numpy()]
        pre_sweep = kz_bars[kz_bars.index <= sweep['sweep_time']]
        ref = pre_sweep if len(pre_sweep) > 0 else kz_bars
        midpoint = (float(ref['high'].max()) + float(ref['low'].min())) / 2

        self._log(f"Signal: {direction.upper()} entry={fvg.entry:.2f} stop={stop:.2f} target={target:.2f}")

        return {
            'actionable':      True,
            'direction':       direction,
            'entry':           fvg.entry,
            'entry_time':      fvg.timestamp,
            'stop':            stop,
            'target':          target,
            'fvg_top':         fvg.top,
            'fvg_bottom':      fvg.bottom,
            'sweep_level':     sweep['stop_level'],
            'sweep_time':      sweep['sweep_time'],
            'swept_pool':      sweep['cluster'].get('source'),
            'swept_cluster':   sweep['cluster'],
            'bms_time':        bms['bms_time'],
            'bms_swing_level': bms['bms_swing_level'],
            'session_midpoint': midpoint,
            'checks':          self.checks,
        }
