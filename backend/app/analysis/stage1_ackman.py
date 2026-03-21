"""Stage 1 – Financial Quality (Ackman's Criteria)

ROIC must be consistently > 10 %.
Debt Ratio must be <= 0.25.
"""

import math

from app.models.schemas import FinancialData, Stage1Result

ROIC_THRESHOLD = 0.10
DEBT_RATIO_THRESHOLD = 0.25


def calc_roic(
    net_income: float,
    dividends: float,
    equity: float,
    debt: float,
    cash: float,
) -> float:
    """ROIC = (Net Income - |Dividends|) / (Equity + Debt - Cash).

    Returns 0.0 when invested capital is non-positive (no meaningful capital base).
    """
    invested_capital = equity + debt - cash
    if invested_capital <= 0:
        return 0.0
    result = (net_income - abs(dividends)) / invested_capital
    return result if math.isfinite(result) else 0.0


def check_roic_consistency(
    roic_values: list[float],
    threshold: float = ROIC_THRESHOLD,
) -> bool:
    if not roic_values:
        return False
    return all(r > threshold for r in roic_values)


def calc_debt_ratio(total_liabilities: float, total_assets: float) -> float:
    """Debt Ratio = Total Liabilities / Total Assets.

    Returns 1.0 (worst case) when total assets is non-positive.
    """
    if total_assets <= 0:
        return 1.0
    result = total_liabilities / total_assets
    return result if math.isfinite(result) else 1.0


def evaluate(data: FinancialData) -> Stage1Result:
    years = min(
        len(data.net_income),
        len(data.total_equity),
        len(data.total_debt),
        len(data.cash),
        len(data.dividends_paid),
    )

    if years == 0:
        return Stage1Result(
            roic_values=[],
            roic_consistent=False,
            debt_ratio=1.0,
            debt_ratio_ok=False,
            passed=False,
        )

    roic_values: list[float] = []
    for i in range(years):
        r = calc_roic(
            data.net_income[i],
            data.dividends_paid[i],
            data.total_equity[i],
            data.total_debt[i],
            data.cash[i],
        )
        roic_values.append(round(r, 4))

    roic_consistent = check_roic_consistency(roic_values)

    debt_ratio = calc_debt_ratio(
        data.total_liabilities[0] if data.total_liabilities else 0.0,
        data.total_assets[0] if data.total_assets else 0.0,
    )
    debt_ratio = round(debt_ratio, 4)
    debt_ratio_ok = debt_ratio <= DEBT_RATIO_THRESHOLD

    return Stage1Result(
        roic_values=roic_values,
        roic_consistent=roic_consistent,
        debt_ratio=debt_ratio,
        debt_ratio_ok=debt_ratio_ok,
        passed=roic_consistent and debt_ratio_ok,
    )
