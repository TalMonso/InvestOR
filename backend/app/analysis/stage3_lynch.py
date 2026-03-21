"""Stage 3 – Growth Premium (Lynch's Calibration)

PEGY Ratio must be <= 1.0.
Growth rates are treated as whole numbers (15 for 15 %).
"""

import math

from app.models.schemas import FinancialData, Stage3Result

PEGY_THRESHOLD = 1.0


def calc_pegy(pe_ratio: float, growth_rate: float, dividend_yield: float) -> float:
    """PEGY = P/E / (Growth Rate + Dividend Yield).

    All inputs should already be whole-number form (e.g. 15 for 15 %).
    Returns inf when denominator is non-positive (stock offers no growth or yield).
    Returns inf for negative P/E (unprofitable company — never passes Lynch screen).
    """
    if pe_ratio <= 0:
        return float("inf")
    denominator = growth_rate + dividend_yield
    if denominator <= 0:
        return float("inf")
    result = pe_ratio / denominator
    return result if math.isfinite(result) else float("inf")


def calc_lynch_fair_value(eps: float, growth_rate: float) -> float:
    """Lynch Fair Value = EPS x Growth Rate (whole number).

    Growth rate must already be a whole number (e.g. 15 for 15 %).
    Example: EPS 4.90, Growth 95.6 -> 4.90 * 95.6 = 468.44.
    Returns 0.0 for non-positive EPS or growth (company is unprofitable or shrinking).
    """
    if eps <= 0 or growth_rate <= 0:
        return 0.0
    result = eps * growth_rate
    return result if math.isfinite(result) else 0.0


def evaluate(data: FinancialData) -> Stage3Result:
    pe = data.trailing_pe

    # Convert decimal rates to whole numbers (0.15 -> 15)
    growth_whole = data.earnings_growth * 100 if math.isfinite(data.earnings_growth) else 0.0
    div_yield_whole = data.dividend_yield * 100 if math.isfinite(data.dividend_yield) else 0.0

    pegy = calc_pegy(pe, growth_whole, div_yield_whole)
    pegy_ok = pegy <= PEGY_THRESHOLD and math.isfinite(pegy)

    lynch_fv = calc_lynch_fair_value(data.eps, growth_whole)

    pegy_display = round(pegy, 4) if math.isfinite(pegy) else 9999.0

    return Stage3Result(
        pegy=pegy_display,
        pegy_ok=pegy_ok,
        lynch_fair_value=round(lynch_fv, 2),
        passed=pegy_ok,
    )
