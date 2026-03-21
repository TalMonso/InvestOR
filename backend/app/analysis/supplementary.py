"""Supplementary metrics – Graham, Greenblatt, Marks, and Reverse DCF."""

import math

from app.models.schemas import FinancialData, SupplementaryResult

REVERSE_DCF_MAX_GROWTH = 0.50
REVERSE_DCF_TOLERANCE = 0.005
_DISCOUNT_RATE = 0.10
_TERMINAL_GROWTH = 0.025
_PROJECTION_YEARS = 5


def calc_graham_number(eps: float, bvps: float) -> float:
    """Graham Number = sqrt(22.5 * EPS * BVPS).

    Returns 0.0 when either input is negative (defensive safeguard).
    """
    if eps <= 0 or bvps <= 0:
        return 0.0
    try:
        result = math.sqrt(22.5 * eps * bvps)
        return result if math.isfinite(result) else 0.0
    except (ValueError, OverflowError):
        return 0.0


def calc_earnings_yield(ebit: float, enterprise_value: float) -> float:
    """Greenblatt's Earnings Yield = EBIT / Enterprise Value.

    Returns 0.0 when enterprise value is non-positive or data is missing.
    """
    if enterprise_value <= 0:
        return 0.0
    try:
        result = ebit / enterprise_value
        return result if math.isfinite(result) else 0.0
    except ZeroDivisionError:
        return 0.0


def calc_interest_coverage(ebit: float, interest_expense: float) -> float:
    """Howard Marks' Interest Coverage = EBIT / Interest Expense.

    Returns 0.0 when interest expense is zero (debt-free or missing data).
    Returns a very large number (999.99) when interest is negligible but EBIT positive.
    """
    if interest_expense <= 0:
        return 999.99 if ebit > 0 else 0.0
    try:
        result = ebit / interest_expense
        if not math.isfinite(result):
            return 0.0
        return min(result, 999.99)
    except ZeroDivisionError:
        return 0.0


def _dcf_uncapped(
    fcf: float,
    growth_rate: float,
    discount_rate: float = _DISCOUNT_RATE,
    years: int = _PROJECTION_YEARS,
    terminal_growth: float = _TERMINAL_GROWTH,
) -> float:
    """DCF without growth capping — used only by the Reverse DCF binary search."""
    if fcf <= 0:
        return 0.0
    growth_rate = max(growth_rate, 0.0)
    total_pv = 0.0
    projected = fcf
    for t in range(1, years + 1):
        projected *= 1 + growth_rate
        total_pv += projected / ((1 + discount_rate) ** t)
    spread = discount_rate - terminal_growth
    if spread <= 0:
        spread = 0.01
    terminal_value = projected * (1 + terminal_growth) / spread
    total_pv += terminal_value / ((1 + discount_rate) ** years)
    return total_pv if math.isfinite(total_pv) else 0.0


def calc_implied_growth_rate(
    fcf: float,
    current_price: float,
    shares_outstanding: float,
    discount_rate: float = _DISCOUNT_RATE,
    terminal_growth: float = _TERMINAL_GROWTH,
) -> float:
    """Reverse DCF: binary search for the growth rate whose 5-year DCF total >= market cap.

    Returns the implied annual growth rate as a decimal (e.g. 0.12 = 12%).
    Returns 0.0 for non-positive FCF (cannot model growth on negative cash flows).
    Returns -1.0 when even max growth can't justify the price (extremely overvalued).
    """
    if fcf <= 0 or shares_outstanding <= 0 or current_price <= 0:
        return 0.0

    market_cap = current_price * shares_outstanding

    low, high = 0.0, REVERSE_DCF_MAX_GROWTH
    for _ in range(100):
        mid = (low + high) / 2
        dcf_total = _dcf_uncapped(fcf, mid, discount_rate, _PROJECTION_YEARS, terminal_growth)

        if abs(dcf_total - market_cap) / max(market_cap, 1.0) < REVERSE_DCF_TOLERANCE:
            return round(mid, 4)

        if dcf_total < market_cap:
            low = mid
        else:
            high = mid

    if low >= REVERSE_DCF_MAX_GROWTH * 0.99:
        return -1.0

    return round((low + high) / 2, 4)


def evaluate(data: FinancialData, owner_earnings: float) -> SupplementaryResult:
    graham = calc_graham_number(data.eps, data.book_value_per_share)
    ey = calc_earnings_yield(data.ebit, data.enterprise_value)
    ic = calc_interest_coverage(data.ebit, data.interest_expense)
    igr = calc_implied_growth_rate(
        owner_earnings,
        data.current_price,
        data.shares_outstanding,
    )

    return SupplementaryResult(
        graham_number=round(graham, 2),
        earnings_yield=round(ey, 4),
        interest_coverage=round(ic, 2),
        implied_growth_rate=round(igr, 4),
    )
