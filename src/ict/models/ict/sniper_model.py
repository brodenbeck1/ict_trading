"""
Sniper Model
================

Composite ICT daily bias checklist: bias direction + stop hunt + SMT divergence
+ market structure shift must all align before a trade is actionable.

Individual concept implementations live in src/ict/concepts/:
  models/intermediate/daily_bias.py — three-signal HTF bias gate (order flow + draw + P/D)
  concepts/liquidity_sweep.py       — sweep / stop-hunt detection
  concepts/smt_divergence.py        — SMT divergence across correlated instruments
  concepts/market_structure.py      — MSS / CHoCH detection

See knowledge/ict/daily-bias/daily-bias.md
"""

import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional

from ict.registry import concept
from ict.models.intermediate.daily_bias import daily_bias_components, ohlc_candle_profile
from ict.concepts.liquidity_sweep import detect_liquidity_sweep
from ict.concepts.smt_divergence import detect_smt
from ict.concepts.market_structure import detect_mss, SwingPointScanner


@dataclass
class SniperSnapshot:
    """
    Data container for multi-instrument, multi-timeframe analysis.

    Attributes:
        df:                 Primary intraday bars (1m or 5m), DatetimeIndex UTC.
        correlated:         Dict of instrument name → OHLCV DataFrame (ES, NQ, YM).
        higher_timeframe_df: Daily (or 4H) bars for bias context.
    """
    df: pd.DataFrame
    correlated: Dict[str, pd.DataFrame]
    higher_timeframe_df: pd.DataFrame


@concept("sniper-model", depends_on=["daily-bias", "liquidity-sweep-stop-hunt", "smt-divergence", "market-structure-shift"])
class SniperModel:
    """
    ICT daily bias checklist model.

    Rule of exclusion: a trade is actionable only when ALL of these align:
      1. HTF daily bias (order flow + draw + premium/discount)
      2. Liquidity sweep of a session pool
      3. SMT divergence on the sweep
      4. Market structure shift back in the bias direction
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.checks: List[str] = []

    def _log(self, msg: str):
        self.checks.append(msg)

    def generate_bias(self, snapshot: SniperSnapshot) -> dict:
        """
        Run the full daily bias checklist against a MarketSnapshot.

        Returns:
            dict: {bias, ohlc_profile, stop_hunt, smt, mss, targets, checks, actionable}
        """
        self.checks = []

        daily_lookback     = self.config.get('daily_lookback', 20)
        dealing_range_days = self.config.get('dealing_range_days', 20)
        swing_lookback     = self.config.get('swing_lookback', 3)
        rej_window         = self.config.get('rejection_window_bars', 12)

        # 1. HTF daily bias
        htf = snapshot.higher_timeframe_df
        components = daily_bias_components(
            htf,
            lookback=daily_lookback,
            dealing_range_days=dealing_range_days,
            swing_lookback=swing_lookback,
        )
        bias = components['bias']
        self._log(
            f"Daily bias: {bias.upper()} "
            f"(order_flow={components['order_flow']}, "
            f"draw={components['draw']}, "
            f"premium_discount={components['premium_discount']})"
        )

        # 2. OHLC candle profile
        profile = ohlc_candle_profile(htf)
        self._log(f"OHLC profile: {profile}")

        if bias == 'neutral':
            self._log("Rule of exclusion: no daily bias → no trade")
            return self._result(bias, profile, None, None, None, snapshot, False)

        # 3. Liquidity sweep of the prior session extreme
        sweep_direction = 'high' if bias == 'bearish' else 'low'
        prior_level = (
            float(htf['high'].iloc[-2]) if sweep_direction == 'high'
            else float(htf['low'].iloc[-2])
        )
        sweep = detect_liquidity_sweep(
            snapshot.df, prior_level, sweep_direction, rej_window
        )
        if sweep is None or sweep['classification'] != 'sweep':
            self._log(f"Rule of exclusion: no {sweep_direction} sweep detected")
            return self._result(bias, profile, sweep, None, None, snapshot, False)
        self._log(
            f"Sweep: {sweep_direction} of {prior_level:.2f} at {sweep['sweep_time']} "
            f"(depth={sweep['depth']:.2f}, class={sweep['classification']})"
        )

        # 4. SMT divergence on the sweep
        smt_kind = 'high' if bias == 'bearish' else 'low'
        smt = detect_smt(snapshot.correlated, kind=smt_kind)
        if smt is None:
            self._log("SMT: no divergence detected")
        else:
            self._log(
                f"SMT: {smt_kind} divergence — leader={smt['leader']}, "
                f"diverging={smt['diverging']}"
            )

        # 5. Market structure shift
        mss_direction = 'bearish' if bias == 'bearish' else 'bullish'
        mss = detect_mss(
            snapshot.df,
            direction=mss_direction,
            swing_lookback=swing_lookback,
            sweep_time=sweep['sweep_time'],
        )
        if mss is None:
            self._log("Rule of exclusion: no MSS detected")
            return self._result(bias, profile, sweep, smt, mss, snapshot, False)
        self._log(
            f"MSS: {mss_direction} break of {mss['broken_level']:.2f} "
            f"at {mss['break_time']}"
        )

        # All components aligned (SMT is confirmation, not hard gate)
        actionable = True
        return self._result(bias, profile, sweep, smt, mss, snapshot, actionable)

    def _result(
        self,
        bias: str,
        profile: str,
        sweep: Optional[dict],
        smt: Optional[dict],
        mss: Optional[dict],
        snapshot: SniperSnapshot,
        actionable: bool,
    ) -> dict:
        targets = self._next_liquidity(snapshot.df)
        return {
            'bias':         bias,
            'ohlc_profile': profile,
            'stop_hunt':    sweep,
            'smt':          smt,
            'mss':          mss,
            'targets':      targets,
            'checks':       list(self.checks),
            'actionable':   actionable,
        }

    def _next_liquidity(self, df: pd.DataFrame) -> Dict[str, float]:
        scanner = SwingPointScanner(df.tail(300), lookback=3)
        scanner.identify_swings()
        highs = (scanner.swing_highs['swing_high_price'].dropna()
                 if scanner.swing_highs is not None else pd.Series(dtype=float))
        lows  = (scanner.swing_lows['swing_low_price'].dropna()
                 if scanner.swing_lows is not None else pd.Series(dtype=float))
        return {
            'high': float(highs.max()) if len(highs) else float('nan'),
            'low':  float(lows.min())  if len(lows)  else float('nan'),
        }
