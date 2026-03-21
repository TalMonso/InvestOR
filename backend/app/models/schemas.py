from __future__ import annotations

from dataclasses import dataclass, field
from pydantic import BaseModel


@dataclass
class FinancialData:
    """Normalized container for all data pulled from yfinance."""

    ticker: str
    current_price: float
    shares_outstanding: float
    trailing_pe: float
    dividend_yield: float  # as decimal, e.g. 0.02 for 2%
    earnings_growth: float  # as decimal, e.g. 0.15 for 15%
    eps: float

    # Scalar fundamentals
    book_value_per_share: float = 0.0
    ebit: float = 0.0
    enterprise_value: float = 0.0
    interest_expense: float = 0.0

    # Multi-year series (most recent first)
    net_income: list[float] = field(default_factory=list)
    total_revenue: list[float] = field(default_factory=list)
    depreciation_amortization: list[float] = field(default_factory=list)
    dividends_paid: list[float] = field(default_factory=list)
    operating_cash_flow: list[float] = field(default_factory=list)

    total_equity: list[float] = field(default_factory=list)
    total_debt: list[float] = field(default_factory=list)
    cash: list[float] = field(default_factory=list)
    total_liabilities: list[float] = field(default_factory=list)
    total_assets: list[float] = field(default_factory=list)
    net_ppe: list[float] = field(default_factory=list)

    capital_expenditure: list[float] = field(default_factory=list)


@dataclass
class Stage1Result:
    roic_values: list[float]
    roic_consistent: bool
    debt_ratio: float
    debt_ratio_ok: bool
    passed: bool


@dataclass
class Stage2Result:
    capex: float
    owner_earnings: float
    dcf_intrinsic_value: float
    iv_per_share: float
    margin_of_safety: float
    mos_ok: bool
    passed: bool


@dataclass
class Stage3Result:
    pegy: float
    pegy_ok: bool
    lynch_fair_value: float
    passed: bool


@dataclass
class Stage4Result:
    b_ratio: float
    full_kelly: float
    half_kelly: float


@dataclass
class SupplementaryResult:
    graham_number: float
    earnings_yield: float
    interest_coverage: float
    implied_growth_rate: float


# --- Pydantic request / response models ---

class AnalyzeRequest(BaseModel):
    ticker: str


class Stage1Response(BaseModel):
    roic_values: list[float]
    roic_consistent: bool
    debt_ratio: float
    debt_ratio_ok: bool
    passed: bool


class Stage2Response(BaseModel):
    capex: float
    owner_earnings: float
    dcf_intrinsic_value: float
    iv_per_share: float
    margin_of_safety: float
    mos_ok: bool
    passed: bool


class Stage3Response(BaseModel):
    pegy: float
    pegy_ok: bool
    lynch_fair_value: float
    passed: bool


class Stage4Response(BaseModel):
    b_ratio: float
    full_kelly: float
    half_kelly: float


class SupplementaryResponse(BaseModel):
    graham_number: float
    earnings_yield: float
    interest_coverage: float
    implied_growth_rate: float


class AnalyzeResponse(BaseModel):
    ticker: str
    current_price: float
    overall_pass: bool
    stage1: Stage1Response
    stage2: Stage2Response
    stage3: Stage3Response
    stage4: Stage4Response | None
    supplementary: SupplementaryResponse
    llm_report: str
    raw_metrics: dict
