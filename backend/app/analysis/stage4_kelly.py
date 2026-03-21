"""Stage 4 – Risk Management & Sizing (Kelly Criterion & Soros)

Only computed when Stages 1-3 all pass.
Half-Kelly is the final recommended allocation.
"""

import math

from app.models.schemas import Stage2Result, Stage4Result

WIN_PROBABILITY = 0.60
MAX_DRAWDOWN = 0.50
MAX_ALLOCATION = 0.20


def calc_b_ratio(
    iv_per_share: float,
    current_price: float,
    max_drawdown: float = MAX_DRAWDOWN,
) -> float:
    """Risk/Reward: potential upside relative to maximum expected loss.

    b = (IV/Share - Price) / (Price * max_drawdown).
    Returns 0.0 when the stock is overvalued or price data is invalid.
    """
    potential_loss = current_price * max_drawdown
    if potential_loss <= 0:
        return 0.0
    result = (iv_per_share - current_price) / potential_loss
    return result if math.isfinite(result) else 0.0


def calc_kelly(p: float, b: float) -> float:
    """Kelly fraction: K = p - (1-p)/b.

    Returns 0.0 for non-positive b (no edge = no bet).
    """
    if b <= 0:
        return 0.0
    result = p - (1 - p) / b
    return result if math.isfinite(result) else 0.0


def calc_half_kelly(k: float) -> float:
    """Soros-adjusted Kelly: cuts the allocation in half and caps at MAX_ALLOCATION."""
    return min(max(k / 2, 0.0), MAX_ALLOCATION)


def evaluate(stage2: Stage2Result, current_price: float) -> Stage4Result:
    if current_price <= 0:
        return Stage4Result(b_ratio=0.0, full_kelly=0.0, half_kelly=0.0)

    b = calc_b_ratio(stage2.iv_per_share, current_price)
    full_k = calc_kelly(WIN_PROBABILITY, b)
    half_k = calc_half_kelly(full_k)

    return Stage4Result(
        b_ratio=round(b, 4),
        full_kelly=round(full_k, 4),
        half_kelly=round(half_k, 4),
    )
