"""Orchestrates the 4-stage analysis pipeline."""

import logging
from dataclasses import asdict

from app.models.schemas import (
    AnalyzeResponse,
    FinancialData,
    Stage1Response,
    Stage1Result,
    Stage2Response,
    Stage2Result,
    Stage3Response,
    Stage3Result,
    Stage4Response,
    Stage4Result,
    SupplementaryResponse,
    SupplementaryResult,
)
from app.analysis import stage1_ackman, stage2_buffett, stage3_lynch, stage4_kelly, supplementary
from app.services.data_fetcher import fetch_financial_data
from app.services.llm_service import generate_report

logger = logging.getLogger(__name__)

_FALLBACK_S1 = Stage1Result(
    roic_values=[], roic_consistent=False, debt_ratio=1.0, debt_ratio_ok=False, passed=False
)
_FALLBACK_S2 = Stage2Result(
    capex=0.0, owner_earnings=0.0, dcf_intrinsic_value=0.0,
    iv_per_share=0.0, margin_of_safety=-1.0, mos_ok=False, passed=False,
)
_FALLBACK_S3 = Stage3Result(pegy=9999.0, pegy_ok=False, lynch_fair_value=0.0, passed=False)
_FALLBACK_SUPP = SupplementaryResult(
    graham_number=0.0, earnings_yield=0.0, interest_coverage=0.0, implied_growth_rate=0.0,
)


async def run_pipeline(ticker: str) -> AnalyzeResponse:
    data: FinancialData = fetch_financial_data(ticker)

    try:
        s1 = stage1_ackman.evaluate(data)
    except Exception:
        logger.exception("Stage 1 failed for %s", ticker)
        s1 = _FALLBACK_S1

    try:
        s2 = stage2_buffett.evaluate(data)
    except Exception:
        logger.exception("Stage 2 failed for %s", ticker)
        s2 = _FALLBACK_S2

    try:
        s3 = stage3_lynch.evaluate(data)
    except Exception:
        logger.exception("Stage 3 failed for %s", ticker)
        s3 = _FALLBACK_S3

    all_passed = s1.passed and s2.passed and s3.passed

    s4: Stage4Result | None = None
    if all_passed:
        try:
            s4 = stage4_kelly.evaluate(s2, data.current_price)
        except Exception:
            logger.exception("Stage 4 failed for %s", ticker)

    try:
        supp = supplementary.evaluate(data, s2.owner_earnings)
    except Exception:
        logger.exception("Supplementary metrics failed for %s", ticker)
        supp = _FALLBACK_SUPP

    report = await generate_report(data, s1, s2, s3, s4, supp, all_passed)

    raw_metrics: dict = {
        "current_price": data.current_price,
        "eps": data.eps,
        "trailing_pe": data.trailing_pe,
        "dividend_yield": data.dividend_yield,
        "earnings_growth": data.earnings_growth,
        "shares_outstanding": data.shares_outstanding,
        **{f"roic_year_{i}": v for i, v in enumerate(s1.roic_values)},
        "debt_ratio": s1.debt_ratio,
        "capex": s2.capex,
        "owner_earnings": s2.owner_earnings,
        "dcf_intrinsic_value": s2.dcf_intrinsic_value,
        "iv_per_share": s2.iv_per_share,
        "margin_of_safety": s2.margin_of_safety,
        "pegy": s3.pegy,
        "lynch_fair_value": s3.lynch_fair_value,
        "graham_number": supp.graham_number,
        "earnings_yield": supp.earnings_yield,
        "interest_coverage": supp.interest_coverage,
        "implied_growth_rate": supp.implied_growth_rate,
    }
    if s4:
        raw_metrics.update(
            b_ratio=s4.b_ratio,
            full_kelly=s4.full_kelly,
            half_kelly=s4.half_kelly,
        )

    return AnalyzeResponse(
        ticker=ticker,
        current_price=data.current_price,
        overall_pass=all_passed,
        stage1=Stage1Response(**asdict(s1)),
        stage2=Stage2Response(**asdict(s2)),
        stage3=Stage3Response(**asdict(s3)),
        stage4=Stage4Response(**asdict(s4)) if s4 else None,
        supplementary=SupplementaryResponse(**asdict(supp)),
        llm_report=report,
        raw_metrics=raw_metrics,
    )
