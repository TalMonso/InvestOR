"""Stage 2 – Valuation & Intrinsic Value (Buffett's Engine)

Owner Earnings (FCF) -> DCF -> Margin of Safety (>= 30 %).
Owner Earnings = Operating Cash Flow - |CapEx|.
"""

import math

from app.models.schemas import FinancialData, Stage2Result

DISCOUNT_RATE = 0.10
PROJECTION_YEARS = 5
TERMINAL_GROWTH = 0.025
MOS_THRESHOLD = 0.30
MAX_GROWTH_RATE = 0.15
DEFAULT_GROWTH_RATE = 0.05


def calc_owner_earnings(operating_cf: float, capex: float) -> float:
    """Owner Earnings (FCF proxy) = Operating Cash Flow - |CapEx|."""
    result = operating_cf - abs(capex)
    return result if math.isfinite(result) else 0.0


def calc_dcf(
    owner_earnings: float,
    growth_rate: float,
    discount_rate: float = DISCOUNT_RATE,
    years: int = PROJECTION_YEARS,
    terminal_growth: float = TERMINAL_GROWTH,
) -> float:
    """Present value of projected Owner Earnings + perpetuity terminal value.

    Returns 0.0 for non-positive owner earnings.
    Growth rate is clamped to MAX_GROWTH_RATE.
    Terminal Value = OE_final * (1 + terminal_growth) / (discount_rate - terminal_growth).
    """
    if owner_earnings <= 0:
        return 0.0

    growth_rate = min(max(growth_rate, 0.0), MAX_GROWTH_RATE)

    total_pv = 0.0
    projected_oe = owner_earnings
    for t in range(1, years + 1):
        projected_oe *= 1 + growth_rate
        total_pv += projected_oe / ((1 + discount_rate) ** t)

    spread = discount_rate - terminal_growth
    if spread <= 0:
        spread = 0.01
    terminal_value = projected_oe * (1 + terminal_growth) / spread
    total_pv += terminal_value / ((1 + discount_rate) ** years)

    return total_pv if math.isfinite(total_pv) else 0.0


def calc_margin_of_safety(iv_per_share: float, current_price: float) -> float:
    """MoS = (IV/Share - Price) / IV/Share.

    Returns -1.0 when intrinsic value is non-positive.
    """
    if iv_per_share <= 0:
        return -1.0
    result = (iv_per_share - current_price) / iv_per_share
    return result if math.isfinite(result) else -1.0


def evaluate(data: FinancialData) -> Stage2Result:
    latest_ocf = data.operating_cash_flow[0] if data.operating_cash_flow else 0.0
    latest_capex = data.capital_expenditure[0] if data.capital_expenditure else 0.0
    capex_abs = abs(latest_capex)

    owner_earnings = calc_owner_earnings(latest_ocf, latest_capex)

    # Negative OE short-circuit: company is burning cash, cannot run DCF
    if owner_earnings <= 0:
        return Stage2Result(
            capex=round(capex_abs, 2),
            owner_earnings=round(owner_earnings, 2),
            dcf_intrinsic_value=0.0,
            iv_per_share=0.0,
            margin_of_safety=-1.0,
            mos_ok=False,
            passed=False,
        )

    growth = data.earnings_growth
    if growth <= 0 or not math.isfinite(growth):
        growth = DEFAULT_GROWTH_RATE
    growth = min(growth, MAX_GROWTH_RATE)

    dcf_value = calc_dcf(owner_earnings, growth)
    shares = data.shares_outstanding if data.shares_outstanding > 0 else 1.0
    iv_per_share = dcf_value / shares
    if not math.isfinite(iv_per_share):
        iv_per_share = 0.0

    mos = calc_margin_of_safety(iv_per_share, data.current_price)
    mos_ok = mos >= MOS_THRESHOLD

    return Stage2Result(
        capex=round(capex_abs, 2),
        owner_earnings=round(owner_earnings, 2),
        dcf_intrinsic_value=round(dcf_value, 2),
        iv_per_share=round(iv_per_share, 2),
        margin_of_safety=round(mos, 4),
        mos_ok=mos_ok,
        passed=mos_ok,
    )
