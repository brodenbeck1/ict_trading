"""
Order Block Detection
=====================

An order block is the last opposing candle before a displacement move that also
sweeps liquidity with its body (not just the wick), then is validated when a
subsequent candle closes back through the OB candle.

Bullish OB:
  - Bearish candle (close < open) whose body close goes below a prior liquidity level
  - Validated: a subsequent candle closes above the OB candle's open
  - Zone: (close, open) of the OB candle

Bearish OB:
  - Bullish candle (close > open) whose body close goes above a prior liquidity level
  - Validated: a subsequent candle closes below the OB candle's open
  - Zone: (open, close) of the OB candle

Liquidity sources (liquidity_source param):
  'pivot'    — basic pivot swing highs/lows (most permissive)
  'hpfs_ob'  — HPFS levels identified via OB-type LTC (body takes prior bar)
  'hpfs_rb'  — HPFS levels identified via RB-type LTC (wick takes, closes inside)
  'rel'      — Relative Equal Highs/Lows (double-stacked liquidity clusters)
"""

import pandas as pd
from dataclasses import dataclass
from typing import Literal

from ict.registry import concept


@dataclass
class OrderBlock:
    timestamp: pd.Timestamp         # timestamp of the OB candle
    direction: str                  # 'bullish' or 'bearish'
    zone_top: float                 # top of OB body zone
    zone_bot: float                 # bottom of OB body zone
    midpoint: float                 # 50% of zone — mean threshold
    sweep_level: float              # the prior liquidity level swept by the body
    liquidity_source: str           # which pool type was swept ('pivot','hpfs_ob','hpfs_rb','rel')
    validated: bool
    validation_time: pd.Timestamp | None = None
    state: str = 'candidate'        # 'candidate' | 'validated' | 'tested' | 'broken'

    @property
    def proximal(self) -> float:
        """Nearest edge: bottom for bullish (retracement enters from above), top for bearish."""
        return self.zone_bot if self.direction == 'bullish' else self.zone_top

    @property
    def distal(self) -> float:
        return self.zone_top if self.direction == 'bullish' else self.zone_bot


# ── Liquidity level builders ──────────────────────────────────────────────────

def _pivot_levels(df: pd.DataFrame, side: str, lookback: int, max_age: int
                  ) -> list[tuple[int, float]]:
    """
    Basic pivot swing levels.

    side: 'low'  → sell-side pools (for bullish OB detection)
          'high' → buy-side pools  (for bearish OB detection)
    """
    levels = []
    n = len(df)
    col = 'low' if side == 'low' else 'high'
    for i in range(lookback, n - lookback):
        window = df[col].iloc[i - lookback: i + lookback + 1]
        val = df[col].iloc[i]
        if val == window.min() if side == 'low' else val == window.max():
            levels.append((i, float(val)))
    return levels


def _hpfs_levels(df: pd.DataFrame, side: str, ltc_type: str) -> list[tuple[int, float]]:
    """
    HPFS levels. Requires the hpfs module.

    side: 'low'  → bullish HPFS lows  (sell-side pools, swept by bullish OB)
          'high' → bearish HPFS highs  (buy-side pools, swept by bearish OB)
    """
    from ict.concepts.hpfs import find_hpfs
    direction = 'bullish' if side == 'low' else 'bearish'
    hpfs_df = find_hpfs(df, direction=direction, ltc_type=ltc_type)
    if hpfs_df.empty:
        return []
    levels = []
    for _, row in hpfs_df.iterrows():
        ts = row['hpfs_time']
        price = float(row['hpfs_level'])
        bar_idx = df.index.get_loc(ts) if ts in df.index else None
        if bar_idx is not None:
            levels.append((int(bar_idx), price))
    return levels


def _rel_levels(df: pd.DataFrame, side: str, swing_lookback: int,
                tolerance: float = 0.0005) -> list[tuple[int, float]]:
    """
    Relative Equal Highs / Lows — double-stacked liquidity clusters.

    side: 'low'  → REL (Relative Equal Lows)
          'high' → REH (Relative Equal Highs)
    """
    from ict.concepts.market_structure import SwingPointScanner
    scanner = SwingPointScanner(df, lookback=swing_lookback)
    scanner.identify_swings()

    if side == 'low':
        clusters = scanner.find_relative_equal_lows(tolerance=tolerance)
        col = 'swing_low_price'
        idx_df = scanner.swing_lows
    else:
        clusters = scanner.find_relative_equal_highs(tolerance=tolerance)
        col = 'swing_high_price'
        idx_df = scanner.swing_highs

    levels = []
    for cluster in clusters:
        price = float(cluster['price'])
        # use the first timestamp in the cluster as the level origin
        ts = cluster['timestamps'][0]
        if ts in df.index:
            levels.append((int(df.index.get_loc(ts)), price))
    return levels


def _build_levels(df: pd.DataFrame, side: str, source: str,
                  swing_lookback: int) -> list[tuple[int, float]]:
    if source == 'pivot':
        return _pivot_levels(df, side, swing_lookback, max_age=0)
    elif source == 'hpfs_ob':
        return _hpfs_levels(df, side, ltc_type='ob')
    elif source == 'hpfs_rb':
        return _hpfs_levels(df, side, ltc_type='rb')
    elif source == 'rel':
        return _rel_levels(df, side, swing_lookback)
    else:
        raise ValueError(f"Unknown liquidity_source: {source!r}. "
                         f"Use 'pivot', 'hpfs_ob', 'hpfs_rb', or 'rel'.")


# ── Main detector ─────────────────────────────────────────────────────────────

@concept("order-block")
def find_order_blocks(
    df: pd.DataFrame,
    direction: str = 'both',
    liquidity_source: Literal['pivot', 'hpfs_ob', 'hpfs_rb', 'rel'] = 'pivot',
    swing_lookback: int = 3,
    max_swing_age: int = 20,
    min_body_pct: float = 0.001,
    validation_window: int = 15,
    validated_only: bool = True,
) -> list[OrderBlock]:
    """
    Scan df for order blocks.

    Args:
        df:                OHLCV DataFrame with DatetimeIndex.
        direction:         'bullish', 'bearish', or 'both'.
        liquidity_source:  Which pool type the OB body must sweep:
                             'pivot'   — basic pivot swing H/L (default, most permissive)
                             'hpfs_ob' — HPFS levels via OB-type LTC (body takes prior bar)
                             'hpfs_rb' — HPFS levels via RB-type LTC (wick takes, closes inside)
                             'rel'     — Relative Equal Highs/Lows (clustered double-stacked pools)
        swing_lookback:    Bars each side for pivot/REL swing identification.
        max_swing_age:     Max bars back to search for a prior level (pivot only).
        min_body_pct:      Minimum OB candle body as fraction of open (filters doji).
        validation_window: Max bars after OB to find the validation candle.
        validated_only:    Return only validated OBs (default True).

    Returns:
        List of OrderBlock in chronological order.
    """
    want_bull = direction in ('bullish', 'both')
    want_bear = direction in ('bearish', 'both')

    sell_side = _build_levels(df, 'low',  liquidity_source, swing_lookback) if want_bull else []
    buy_side  = _build_levels(df, 'high', liquidity_source, swing_lookback) if want_bear else []

    obs: list[OrderBlock] = []

    for i in range(1, len(df) - 1):
        row = df.iloc[i]
        o, h, l, c = float(row['open']), float(row['high']), float(row['low']), float(row['close'])
        body = abs(c - o)
        if body / o < min_body_pct:
            continue

        # ── Bullish OB: bearish candle body closes below a sell-side level ────
        if want_bull and c < o:
            prior = [(j, p) for j, p in sell_side
                     if j < i and (liquidity_source != 'pivot' or (i - j) <= max_swing_age)]
            if prior:
                j_low, swing_low = max(prior, key=lambda x: x[0])
                if c < swing_low:
                    # skip if next candle continues the sweep (keep last in the run)
                    nxt = df.iloc[i + 1]
                    if float(nxt['close']) < float(nxt['open']) and float(nxt['close']) < swing_low:
                        continue
                    valid_idx = None
                    for k in range(i + 1, min(i + validation_window + 1, len(df))):
                        if float(df.iloc[k]['close']) > o:
                            valid_idx = k
                            break
                    is_valid = valid_idx is not None
                    if validated_only and not is_valid:
                        continue
                    obs.append(OrderBlock(
                        timestamp=df.index[i],
                        direction='bullish',
                        zone_top=o,
                        zone_bot=c,
                        midpoint=(o + c) / 2,
                        sweep_level=swing_low,
                        liquidity_source=liquidity_source,
                        validated=is_valid,
                        validation_time=df.index[valid_idx] if is_valid else None,
                        state='validated' if is_valid else 'candidate',
                    ))

        # ── Bearish OB: bullish candle body closes above a buy-side level ─────
        elif want_bear and c > o:
            prior = [(j, p) for j, p in buy_side
                     if j < i and (liquidity_source != 'pivot' or (i - j) <= max_swing_age)]
            if prior:
                j_high, swing_high = max(prior, key=lambda x: x[0])
                if c > swing_high:
                    nxt = df.iloc[i + 1]
                    if float(nxt['close']) > float(nxt['open']) and float(nxt['close']) > swing_high:
                        continue
                    valid_idx = None
                    for k in range(i + 1, min(i + validation_window + 1, len(df))):
                        if float(df.iloc[k]['close']) < o:
                            valid_idx = k
                            break
                    is_valid = valid_idx is not None
                    if validated_only and not is_valid:
                        continue
                    obs.append(OrderBlock(
                        timestamp=df.index[i],
                        direction='bearish',
                        zone_top=c,
                        zone_bot=o,
                        midpoint=(o + c) / 2,
                        sweep_level=swing_high,
                        liquidity_source=liquidity_source,
                        validated=is_valid,
                        validation_time=df.index[valid_idx] if is_valid else None,
                        state='validated' if is_valid else 'candidate',
                    ))

    return obs
