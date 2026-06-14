"""
Daily Bias (Intermediate Model)
================================

Three-signal gate: order flow + draw-on-liquidity + 4H structure must all
agree. Premium/discount and prior-day midpoint are computed as reference
signals for model-level entry-zone filtering but are NOT in the gate
(including P/D in the gate causes structural contradiction because a falling
market is by definition in a discount zone).

Bias is computed once pre-session from the daily chart and held fixed for the
day. If signals conflict the result is 'neutral' → no trade (rule of exclusion).

Lives in models/intermediate/ because it composes multiple concepts rather than
implementing a single primitive — it is itself a building block for full models.

See knowledge/ict/daily-bias/daily-bias.md
"""

from __future__ import annotations

import pandas as pd
from typing import Optional

from ict.registry import concept
from ict.concepts.draw_on_liquidity import draw_on_liquidity
from ict.concepts.premium_discount import premium_discount
from ict.concepts.ohlc_profiles import ohlc_candle_profile  # noqa: F401


@concept("daily-bias", depends_on=["draw-on-liquidity", "premium-discount", "ohlc-candle-profiles"])
def daily_bias(
    daily_df: pd.DataFrame,
    lookback: int = 20,
    dealing_range_days: int = 20,
    swing_lookback: int = 3,
    df_4h: Optional[pd.DataFrame] = None,
    four_h_gate: str = 'soft',
) -> str:
    """
    Compute ICT daily bias from the daily (and optionally 4H) chart.

    All gate signals must agree; otherwise returns 'neutral'.

    Args:
        daily_df:           Daily OHLCV bars, DatetimeIndex.
        lookback:           Bars for order-flow scoring.
        dealing_range_days: Bars for the dealing range (draw + premium/discount).
        swing_lookback:     Bar lookback for swing detection inside draw-on-liquidity.
        df_4h:              4H OHLCV bars for structure confirmation. When provided
                            and non-neutral, must align with daily order flow or bias
                            is neutral.

    Returns:
        'bullish' | 'bearish' | 'neutral'
    """
    components = daily_bias_components(daily_df, lookback, dealing_range_days, swing_lookback, df_4h, four_h_gate)
    return components['bias']


def daily_bias_components(
    daily_df: pd.DataFrame,
    lookback: int = 20,
    dealing_range_days: int = 20,
    swing_lookback: int = 3,
    df_4h: Optional[pd.DataFrame] = None,
    four_h_gate: str = 'soft',
) -> dict:
    """
    Return each sub-signal plus the combined bias verdict.

    Gate signals (all must agree for a non-neutral result):
        order_flow       — daily candle direction over ``lookback`` bars
        draw             — nearest unswept swing pool direction
        four_h_structure — 4H order flow; behaviour controlled by ``four_h_gate``:
                           'soft' (default) — neutral 4H abstains, does not veto;
                           'hard' — 4H must actively agree, neutral vetoes.

    Reference signals (returned for context, NOT in the gate):
        premium_discount   — current price position relative to dealing range
        prior_day_midpoint — prior day close vs prior day midpoint (bullish/bearish/neutral)

    Returns:
        dict with keys: order_flow, draw, four_h_structure, premium_discount,
                        prior_day_midpoint, bias
    """
    neutral = {
        'order_flow': 'neutral',
        'draw': 'neutral',
        'four_h_structure': 'neutral',
        'premium_discount': 'neutral',
        'prior_day_midpoint': 'neutral',
        'bias': 'neutral',
    }
    if daily_df is None or len(daily_df) < max(lookback, 3):
        return neutral

    order_flow    = _order_flow(daily_df, lookback)
    draw          = draw_on_liquidity(daily_df, dealing_range_days, swing_lookback)
    prem_disc     = premium_discount(daily_df, dealing_range_days)
    four_h        = _four_h_structure(df_4h, lookback) if df_4h is not None else 'neutral'
    prior_day_mid = _prior_day_midpoint(daily_df)

    # Gate: order_flow and draw must agree.
    # 4H gate: 'soft' — neutral 4H abstains (does not veto an otherwise valid signal).
    #          'hard' — 4H must actively agree; neutral vetoes.
    if four_h_gate == 'hard':
        if order_flow == draw == four_h == 'bullish':
            bias = 'bullish'
        elif order_flow == draw == four_h == 'bearish':
            bias = 'bearish'
        else:
            bias = 'neutral'
    else:  # soft (default)
        if order_flow == draw == 'bullish' and four_h in ('bullish', 'neutral'):
            bias = 'bullish'
        elif order_flow == draw == 'bearish' and four_h in ('bearish', 'neutral'):
            bias = 'bearish'
        else:
            bias = 'neutral'

    return {
        'order_flow':        order_flow,
        'draw':              draw,
        'four_h_structure':  four_h,
        'premium_discount':  prem_disc,
        'prior_day_midpoint': prior_day_mid,
        'bias':              bias,
    }


# ---------------------------------------------------------------------------
# Sub-signals
# ---------------------------------------------------------------------------

def _order_flow(daily_df: pd.DataFrame, n: int) -> str:
    """Daily order flow: net direction over last n closed bars."""
    recent = daily_df.tail(n).dropna(subset=['open', 'close'])
    if len(recent) < 2:
        return 'neutral'
    net  = recent['close'].iloc[-1] - recent['close'].iloc[0]
    up   = int((recent['close'] > recent['open']).sum())
    down = int((recent['close'] < recent['open']).sum())
    if net > 0 and up >= down:
        return 'bullish'
    if net < 0 and down >= up:
        return 'bearish'
    return 'neutral'


def _four_h_structure(df_4h: pd.DataFrame, lookback: int) -> str:
    """
    4H structure confirmation — same order-flow logic applied to 4H bars.

    Uses lookback * 6 bars (each daily bar ≈ 6 four-hour bars) so the 4H
    window covers roughly the same calendar span as the daily lookback.
    """
    if df_4h is None or len(df_4h) < 2:
        return 'neutral'
    n = max(lookback * 6, 6)
    return _order_flow(df_4h.tail(n), n)


def _prior_day_midpoint(daily_df: pd.DataFrame) -> str:
    """
    Prior day close relative to prior day midpoint.

    Bullish when the prior day closed above its own midpoint (upper half of range),
    suggesting bullish carry into the current session. Bearish when below.
    Neutral if data is insufficient or the prior day's range is zero.
    """
    if daily_df is None or len(daily_df) < 2:
        return 'neutral'
    prior = daily_df.iloc[-2]
    rng   = float(prior['high']) - float(prior['low'])
    if rng == 0:
        return 'neutral'
    midpoint = float(prior['low']) + rng / 2
    close    = float(prior['close'])
    if close > midpoint:
        return 'bullish'
    if close < midpoint:
        return 'bearish'
    return 'neutral'
