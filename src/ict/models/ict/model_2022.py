"""
ICT 2022 Model
==================================

``context -> sweep -> MSS w/ displacement -> retrace into FVG -> deliver to draw``

Checklist (bearish — inverted for bullish):
  1. Daily bias  — order flow + draw + 4H structure must agree; P/D is a reference signal.
  2. Pool set    — PDH/PDL, opening range, REH/REL from the 15m chart.
  3. Sweep       — a buy-side pool raided inside a killzone.
  4. MSS         — 2m close through the prior swing with displacement + FVG.
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
from ict.concepts.sessions import opening_range, ons_range, chicago_range
from ict.concepts.targets import find_liquidity_target
from ict.utils.time_utils import localize_like


@dataclass
class Model2022Snapshot:
    """
    Attributes:
        df_2m:        2-minute bars for the session (entry timeframe).
        df_15m:       15-minute bars for pool detection.
        df_daily:     Daily bars for bias (pre-session).
        session_date: Calendar date being analyzed (tz-naive local date).
        df_4h:        4-hour bars for bias confirmation (optional).
    """
    df_2m: pd.DataFrame
    df_15m: pd.DataFrame
    df_daily: pd.DataFrame
    session_date: pd.Timestamp
    df_4h: Optional[pd.DataFrame] = None


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
        max_bars_sweep_to_mss int    Cap on 2m bars between sweep and MSS (default 30)
        target_min_rr         float  Minimum R:R; also the fixed fallback (default 3.0)
        max_stop_pts          float  Max allowed stop distance in points; wider stops excluded (default 20.0)
    """

    # The opening-range window is owned by the sessions-and-ranges concept; its
    # canonical default lives in that concept's frontmatter (see __init__). The
    # values below are only fallbacks if the frontmatter can't be read.
    DEFAULT_CONFIG = {
        # ── Timing ────────────────────────────────────────────────────────────
        'eq_tolerance_pts': 5.0,
        'swing_lookback': 1,
        'killzones': [('02:00', '05:00'), ('07:00', '10:00'), ('13:30', '16:00')],
        'daily_lookback': 5,
        'dealing_range_days': 20,
        'reh_lookback_days': 5,
        'opening_range_start': '09:30',
        'opening_range_minutes': 30,
        'max_bars_sweep_to_mss': 30,
        # ── Pool component toggles ─────────────────────────────────────────────
        'use_pdh_pdl': True,
        'use_ons': True,
        'use_chicago_prior': True,
        'use_chicago_same_day': True,
        'use_opening_range': True,
        'use_reh_rel': True,
        # ── Stop placement ────────────────────────────────────────────────────
        # stop_mode: 'wick'  → stop at swept wick extreme (capped by max_stop_pts)
        #            'atr'   → stop at entry ± stop_atr_mult × ATR(stop_atr_period)
        #            'fixed' → stop at entry ± stop_fixed_pts
        'stop_mode': 'wick',
        'stop_atr_period': 14,
        'stop_atr_mult': 1.0,
        'stop_fixed_pts': 20.0,
        'max_stop_pts': 20.0,           # cap applied after wick/atr/fixed placement
        # ── Target ────────────────────────────────────────────────────────────
        'target_min_rr': 3.0,
        # ── Daily bias ────────────────────────────────────────────────────────
        # four_h_gate: 'soft' — neutral 4H abstains (does not veto daily signal)
        #              'hard' — 4H must actively agree; neutral 4H vetoes
        'four_h_gate': 'soft',
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

    def _daily_bias(self, daily_df: pd.DataFrame, df_4h: Optional[pd.DataFrame] = None) -> str:
        components = daily_bias_components(
            daily_df,
            lookback=self.config['daily_lookback'],
            dealing_range_days=self.config['dealing_range_days'],
            swing_lookback=self.config['swing_lookback'],
            df_4h=df_4h,
            four_h_gate=self.config.get('four_h_gate', 'soft'),
        )
        bias = components['bias']
        if bias == 'neutral':
            self._log(
                f"Daily bias: neutral (order_flow={components['order_flow']}, "
                f"draw={components['draw']}, "
                f"4H={components['four_h_structure']}, "
                f"premium_discount={components['premium_discount']})"
            )
        else:
            self._log(
                f"Daily bias: {bias.upper()} "
                f"(order_flow={components['order_flow']}, draw={components['draw']}, "
                f"4H={components['four_h_structure']}, "
                f"prior_day_mid={components['prior_day_midpoint']})"
            )
        return bias

    # ------------------------------------------------------------------
    # Step 2: Session liquidity pool set
    # ------------------------------------------------------------------

    def _build_pools(self, snapshot: Model2022Snapshot, before: pd.Timestamp) -> dict:
        """PDH/PDL + opening range + REH/REL. Returns {highs: [...], lows: [...]}."""
        highs: list = []
        lows:  list = []

        session_open = pd.Timestamp(f"{snapshot.session_date.date()} 00:00",
                                    tz='America/New_York').tz_convert('UTC')

        if self.config['use_pdh_pdl']:
            daily = snapshot.df_daily
            if daily is not None and len(daily) > 0:
                before_daily = localize_like(before, daily.index)
                prior = daily[daily.index < before_daily]
                if len(prior) > 0:
                    pdh = float(prior['high'].iloc[-1])
                    pdl = float(prior['low'].iloc[-1])
                    pdh_ts = prior.index[-1]
                    highs.append({'extreme_price': pdh, 'price': pdh, 'source': 'PDH',
                                  'timestamps': [pdh_ts], 'formed_at': session_open})
                    lows.append({'extreme_price': pdl, 'price': pdl, 'source': 'PDL',
                                 'timestamps': [pdh_ts], 'formed_at': session_open})

        if self.config['use_chicago_prior']:
            prior_date = snapshot.session_date - pd.Timedelta(days=1)
            chicago_prior = chicago_range(snapshot.df_2m, prior_date)
            if chicago_prior is not None:
                highs.append({'extreme_price': chicago_prior['high'], 'price': chicago_prior['high'],
                              'source': 'Chicago-prior-high', 'timestamps': [chicago_prior['end']],
                              'formed_at': session_open})
                lows.append({'extreme_price': chicago_prior['low'], 'price': chicago_prior['low'],
                             'source': 'Chicago-prior-low', 'timestamps': [chicago_prior['end']],
                             'formed_at': session_open})

        if self.config['use_chicago_same_day']:
            chicago_today = chicago_range(snapshot.df_2m, snapshot.session_date)
            if chicago_today is not None:
                highs.append({'extreme_price': chicago_today['high'], 'price': chicago_today['high'],
                              'source': 'Chicago-high', 'timestamps': [chicago_today['end']],
                              'formed_at': chicago_today['end']})
                lows.append({'extreme_price': chicago_today['low'], 'price': chicago_today['low'],
                             'source': 'Chicago-low', 'timestamps': [chicago_today['end']],
                             'formed_at': chicago_today['end']})

        if self.config['use_ons']:
            ons = ons_range(snapshot.df_2m, snapshot.session_date)
            if ons is not None:
                highs.append({'extreme_price': ons['high'], 'price': ons['high'], 'source': 'ONS-high',
                              'timestamps': [ons['end']], 'formed_at': ons['end']})
                lows.append({'extreme_price': ons['low'], 'price': ons['low'], 'source': 'ONS-low',
                             'timestamps': [ons['end']], 'formed_at': ons['end']})

        if self.config['use_opening_range']:
            orng = opening_range(
                snapshot.df_2m, snapshot.session_date,
                minutes=self.config['opening_range_minutes'],
                start_ny=self.config['opening_range_start'],
            )
            if orng is not None:
                highs.append({'extreme_price': orng['high'], 'price': orng['high'], 'source': 'OR-high',
                              'timestamps': [orng['high_time']], 'formed_at': orng['range_end'],
                              'range_start': orng['range_start'], 'range_end': orng['range_end'],
                              'range_low': orng['low']})
                lows.append({'extreme_price': orng['low'],  'price': orng['low'],  'source': 'OR-low',
                             'timestamps': [orng['low_time']], 'formed_at': orng['range_end'],
                             'range_start': orng['range_start'], 'range_end': orng['range_end'],
                             'range_high': orng['high']})

        if self.config['use_reh_rel']:
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
        df_2m: pd.DataFrame,
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
        kz_times = set(df_2m.index[kz_mask.to_numpy()])

        best = None
        for pool in pools:
            lvl = pool['extreme_price']
            ts, row = first_breach(df_2m, lvl, side, after=pool.get('formed_at'))
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
    # Target pool validity filter
    # ------------------------------------------------------------------

    def _live_target_pools(
        self,
        df_2m: pd.DataFrame,
        pools: list,
        direction: str,
        as_of: pd.Timestamp,
    ) -> list:
        """
        Return only pools that have NOT yet been run as of as_of.

        A target pool is dead once price has already traded through it — there's
        no resting liquidity left to draw toward. The sweep side for a target is
        the opposite of entry: short targets are sell-side (price must trade DOWN
        through them), long targets are buy-side (price must trade UP through them).
        """
        side = 'low' if direction == 'short' else 'high'
        as_of = localize_like(as_of, df_2m.index)
        live = []
        for pool in pools:
            lvl = pool['extreme_price']
            formed_at = pool.get('formed_at')
            ts, _ = first_breach(df_2m, lvl, side, after=formed_at)
            if ts is None or ts > as_of:
                live.append(pool)
        if len(live) < len(pools):
            self._log(f"Target pools: {len(pools) - len(live)} already run, {len(live)} live")
        return live

    # ------------------------------------------------------------------
    # Step 4: MSS with displacement on 2m
    # ------------------------------------------------------------------

    def _detect_bms(
        self,
        df_2m: pd.DataFrame,
        direction: str,
        after_time: pd.Timestamp,
    ) -> Optional[dict]:
        """Thin wrapper around detect_mss; adds df_after slice for FVG search."""
        after_time = localize_like(after_time, df_2m.index)
        result = detect_mss(
            df_2m,
            direction=direction,
            swing_lookback=self.config['swing_lookback'],
            max_bars_after_sweep=self.config['max_bars_sweep_to_mss'],
            sweep_time=after_time,
        )
        if result is None:
            return None

        cutoff = df_2m.index.get_indexer([after_time], method='nearest')[0]
        end     = min(cutoff + self.config['max_bars_sweep_to_mss'] + 1, len(df_2m))
        df_after = df_2m.iloc[cutoff:end]
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

    def generate_signal(
        self,
        snapshot: Model2022Snapshot,
        force_direction: Optional[str] = None,
    ) -> dict:
        """Evaluate one session for a valid 2022-model setup.

        Args:
            force_direction: 'bearish' or 'bullish' — skips the daily bias gate
                and evaluates only that side. Pass None to use daily bias normally.
        """
        self.checks = []
        base = {
            'actionable': False, 'direction': None,
            'entry': None, 'entry_time': None,
            'stop': None, 'target': None,
            'fvg_top': None, 'fvg_bottom': None,
            'sweep_level': None, 'session_midpoint': None,
            'checks': self.checks,
        }

        # 1. Daily bias (skipped when force_direction is provided)
        if force_direction is not None:
            bias = force_direction
            self._log(f"Daily bias: FORCED {bias.upper()} (gate bypassed)")
        else:
            bias = self._daily_bias(snapshot.df_daily, df_4h=snapshot.df_4h)
            if bias == 'neutral':
                self._log("Rule of exclusion: no daily bias → no trade")
                return base

        direction = 'short' if bias == 'bearish' else 'long'

        # 1b. Premium/discount entry zone (soft check — log misalignment)
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
        kz_mask = session_mask(snapshot.df_2m, snapshot.session_date, self.config['killzones'])
        if int(kz_mask.sum()) < 5:
            self._log("Rule of exclusion: insufficient killzone data")
            return base
        sweep = self._detect_sweep(snapshot.df_2m, kz_mask, entry_pools, bias)
        if sweep is None:
            self._log("Rule of exclusion: no stop hunt in killzone")
            return base

        # 4. MSS
        bms = self._detect_bms(snapshot.df_2m, bias, sweep['sweep_time'])
        if bms is None:
            self._log("Rule of exclusion: no MSS after stop hunt")
            return base

        # 5. FVG
        fvg = self._find_entry_fvg(bms, bias)
        if fvg is None:
            self._log("Rule of exclusion: no FVG at MSS displacement")
            return base

        # 6. Stop placement — mode-dependent, then capped by max_stop_pts.
        stop_mode = self.config['stop_mode']
        if stop_mode == 'wick':
            stop = sweep['stop_level']
        elif stop_mode == 'atr':
            period = self.config['stop_atr_period']
            mult   = self.config['stop_atr_mult']
            idx    = snapshot.df_2m.index.searchsorted(fvg.timestamp)
            win    = snapshot.df_2m.iloc[max(0, idx - period): idx]
            if len(win) >= 2:
                tr = pd.concat([
                    win['high'] - win['low'],
                    (win['high'] - win['close'].shift()).abs(),
                    (win['low']  - win['close'].shift()).abs(),
                ], axis=1).max(axis=1)
                atr = float(tr.mean())
            else:
                atr = self.config['max_stop_pts']
            stop = fvg.entry + atr * mult if direction == 'short' else fvg.entry - atr * mult
            self._log(f"ATR stop: ATR={atr:.2f} × {mult} → stop={stop:.2f}")
        elif stop_mode == 'fixed':
            pts  = self.config['stop_fixed_pts']
            stop = fvg.entry + pts if direction == 'short' else fvg.entry - pts
            self._log(f"Fixed stop: ±{pts} pts → stop={stop:.2f}")
        else:
            raise ValueError(f"Unknown stop_mode: {stop_mode!r}  (expected 'wick', 'atr', 'fixed')")

        if direction == 'short' and stop <= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not above entry {fvg.entry:.2f}")
            return base
        if direction == 'long' and stop >= fvg.entry:
            self._log(f"Rule of exclusion: stop {stop:.2f} not below entry {fvg.entry:.2f}")
            return base

        max_stop = self.config['max_stop_pts']
        if abs(stop - fvg.entry) > max_stop:
            stop = fvg.entry + max_stop if direction == 'short' else fvg.entry - max_stop
            self._log(f"Stop capped at {max_stop} pts: {stop:.2f}")

        # 7. Target — filter to pools not yet run as of entry time, then find
        #    the nearest opposing pool meeting the R:R floor.
        live_targets = self._live_target_pools(
            snapshot.df_2m, target_pools, direction, fvg.timestamp,
        )
        target = find_liquidity_target(
            direction, entry=fvg.entry, stop=stop,
            target_pools=live_targets, min_rr=self.config['target_min_rr'],
        )
        rr = abs(target - fvg.entry) / abs(stop - fvg.entry) if stop != fvg.entry else 0
        self._log(f"Target: {target:.2f}  R:R={rr:.2f}")

        # Session midpoint (chart context) — over the killzone bars up to the sweep
        kz_bars = snapshot.df_2m[kz_mask.to_numpy()]
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
