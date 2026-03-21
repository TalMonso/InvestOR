"""Fetches and normalizes financial data from yfinance."""

import logging
import math

import numpy as np
import yfinance as yf

from app.models.schemas import FinancialData

logger = logging.getLogger(__name__)


def _safe_list(series, length: int = 4) -> list[float]:
    """Extract up to `length` floats from a pandas Series, replacing NaN/Inf with 0."""
    if series is None:
        return [0.0] * length
    try:
        vals = series.head(length).tolist()
    except Exception:
        return [0.0] * length
    cleaned: list[float] = []
    for v in vals:
        try:
            f = float(v)
            cleaned.append(f if math.isfinite(f) else 0.0)
        except (TypeError, ValueError):
            cleaned.append(0.0)
    return cleaned


def _safe_scalar(val, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        f = float(val)
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


def _get_row(df, labels: list[str], length: int = 4) -> list[float]:
    """Try multiple row labels and return the first match as a list of floats."""
    if df is None:
        return [0.0] * length
    try:
        if df.empty:
            return [0.0] * length
    except Exception:
        return [0.0] * length
    for label in labels:
        if label in df.index:
            return _safe_list(df.loc[label], length)
    return [0.0] * length


def fetch_financial_data(ticker: str) -> FinancialData:
    """Fetch financial statements from yfinance and return a normalized FinancialData.

    Raises ValueError with a user-friendly message on unrecoverable failures.
    """
    try:
        stock = yf.Ticker(ticker)
    except Exception as exc:
        raise ValueError(f"Failed to create yfinance Ticker for '{ticker}': {exc}")

    # ── Validate that the ticker exists ──
    try:
        info = stock.info or {}
    except Exception as exc:
        raise ValueError(
            f"Could not fetch info for '{ticker}' — the ticker may be invalid "
            f"or yfinance may be rate-limited: {exc}"
        )

    current_price = _safe_scalar(
        info.get("currentPrice") or info.get("regularMarketPrice")
    )
    if current_price <= 0:
        raise ValueError(
            f"No valid price found for '{ticker}'. "
            "The ticker may be delisted, misspelled, or unsupported."
        )

    # ── Pull financial statements (may be empty for some tickers) ──
    try:
        income = stock.income_stmt
    except Exception:
        logger.warning("Could not fetch income statement for %s", ticker)
        income = None

    try:
        balance = stock.balance_sheet
    except Exception:
        logger.warning("Could not fetch balance sheet for %s", ticker)
        balance = None

    try:
        cashflow = stock.cashflow
    except Exception:
        logger.warning("Could not fetch cash flow for %s", ticker)
        cashflow = None

    shares = _safe_scalar(info.get("sharesOutstanding"), 1.0)
    if shares <= 0:
        shares = 1.0

    pe = _safe_scalar(info.get("trailingPE"))
    div_yield = _safe_scalar(info.get("dividendYield"))
    growth = _safe_scalar(info.get("earningsGrowth"))
    eps = _safe_scalar(info.get("trailingEps"))
    bvps = _safe_scalar(info.get("bookValue"))
    enterprise_value = _safe_scalar(info.get("enterpriseValue"))

    net_income = _get_row(income, ["Net Income", "Net Income Common Stockholders"])
    total_revenue = _get_row(income, ["Total Revenue", "Operating Revenue"])

    ebit_row = _get_row(income, ["EBIT", "Operating Income"], length=1)
    ebit = ebit_row[0] if ebit_row else 0.0

    interest_row = _get_row(income, ["Interest Expense", "Net Interest Income"], length=1)
    interest_expense = abs(interest_row[0]) if interest_row else 0.0

    if all(v == 0.0 for v in net_income) and all(v == 0.0 for v in total_revenue):
        logger.warning(
            "All income statement values are zero for %s — financial data may be unavailable",
            ticker,
        )

    return FinancialData(
        ticker=ticker,
        current_price=current_price,
        shares_outstanding=shares,
        trailing_pe=pe,
        dividend_yield=div_yield,
        earnings_growth=growth,
        eps=eps,
        book_value_per_share=bvps,
        ebit=ebit,
        enterprise_value=enterprise_value,
        interest_expense=interest_expense,
        net_income=net_income,
        total_revenue=total_revenue,
        depreciation_amortization=_get_row(
            cashflow,
            ["Depreciation And Amortization", "Depreciation & Amortization"],
        ),
        dividends_paid=_get_row(
            cashflow,
            ["Common Stock Dividend Paid", "Payment Of Dividends"],
        ),
        operating_cash_flow=_get_row(
            cashflow,
            [
                "Operating Cash Flow",
                "Cash Flow From Continuing Operating Activities",
                "Total Cash From Operating Activities",
            ],
        ),
        total_equity=_get_row(
            balance,
            [
                "Total Equity Gross Minority Interest",
                "Stockholders Equity",
                "Total Stockholders Equity",
            ],
        ),
        total_debt=_get_row(balance, ["Total Debt", "Long Term Debt"]),
        cash=_get_row(
            balance,
            [
                "Cash And Cash Equivalents",
                "Cash Cash Equivalents And Short Term Investments",
            ],
        ),
        total_liabilities=_get_row(
            balance,
            ["Total Liabilities Net Minority Interest", "Total Liabilities"],
        ),
        total_assets=_get_row(balance, ["Total Assets"]),
        net_ppe=_get_row(
            balance,
            ["Net PPE", "Property Plant And Equipment Net", "Gross PPE"],
        ),
        capital_expenditure=_get_row(
            cashflow, ["Capital Expenditure", "Purchase Of PPE"]
        ),
    )
