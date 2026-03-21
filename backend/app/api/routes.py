import logging
import re

from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.services.pipeline import run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()

_TICKER_RE = re.compile(r"^[A-Z0-9.\-]{1,10}$")


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    ticker = request.ticker.strip().upper()

    if not ticker:
        raise HTTPException(status_code=400, detail="Ticker is required.")

    if not _TICKER_RE.match(ticker):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ticker format: '{ticker}'. "
            "Use 1-10 uppercase letters, digits, dots, or hyphens (e.g. AAPL, BRK.B).",
        )

    try:
        result = await run_pipeline(ticker)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.exception("Unhandled error analysing %s", ticker)
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed for '{ticker}': {exc}",
        )
