"""
Targets & Exits
===============

Liquidity-to-liquidity targeting with a minimum R:R gate.

See knowledge/ict/entries/targets-and-exits.md
"""

from ict.registry import concept


@concept("targets-and-exits")
def find_liquidity_target(
    direction: str,
    entry: float,
    stop: float,
    target_pools: list,
    min_rr: float = 3.0,
) -> float:
    """
    Compute the take-profit target using the nearest opposing liquidity pool
    that satisfies the minimum R:R requirement. Falls back to a fixed R multiple
    when no pool qualifies or none exists.

    Args:
        direction:    'long' or 'short'.
        entry:        Limit entry price.
        stop:         Structural stop price (beyond the swept extreme).
        target_pools: List of pool dicts with at minimum {'extreme_price': float}.
        min_rr:       Minimum reward-to-risk ratio required (default 3.0).

    Returns:
        Target price (float). Always satisfies the min_rr floor.
    """
    risk = abs(stop - entry)
    floor = (entry - min_rr * risk) if direction == 'short' else (entry + min_rr * risk)

    if direction == 'short':
        candidates = [p['extreme_price'] for p in target_pools if p['extreme_price'] < entry]
        nearest = max(candidates) if candidates else None
    else:
        candidates = [p['extreme_price'] for p in target_pools if p['extreme_price'] > entry]
        nearest = min(candidates) if candidates else None

    if nearest is not None and risk > 0 and abs(entry - nearest) / risk >= min_rr:
        return float(nearest)

    return float(floor)


def rr_ratio(entry: float, stop: float, target: float) -> float:
    """Compute planned R:R. Returns 0.0 when risk is zero."""
    risk = abs(stop - entry)
    if risk == 0:
        return 0.0
    return abs(target - entry) / risk
