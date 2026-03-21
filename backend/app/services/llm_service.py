"""LLM integration – Ollama only. Builds a structured prompt and calls the local Ollama API."""

import logging
import os

import httpx
from dotenv import load_dotenv

from app.models.schemas import (
    FinancialData,
    Stage1Result,
    Stage2Result,
    Stage3Result,
    Stage4Result,
    SupplementaryResult,
)

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Board of Legendary Investors — a collective voice channeling the
philosophies of Benjamin Graham, Joel Greenblatt, Howard Marks, Warren Buffett, Peter Lynch,
George Soros, and Bill Ackman. You must provide a deep, detailed, and easily digestible
investment report based ONLY on the numerical metrics and pass/fail results provided below.
Do not fabricate data.

Structure your report as follows:

1. **Executive Summary** – one-paragraph verdict (BUY / REJECT).

2. **Stage 1 – Financial Quality (Ackman)** – discuss ROIC consistency and debt ratio.

3. **Stage 2 – Intrinsic Value (Buffett)** – discuss Owner Earnings (FCF), DCF valuation,
   and Margin of Safety.

4. **Stage 3 – Growth Premium (Lynch)** – discuss PEGY ratio and Lynch Fair Value.

5. **Stage 4 – Risk Sizing (Kelly / Soros)** – discuss the Kelly Criterion allocation.
   When explaining the Half-Kelly recommendation you MUST explicitly reference George Soros's
   "Principle of Fallibility" (all human constructs, including valuation models, are inherently
   flawed) and "Reflexivity" (market participants' biased views can create self-reinforcing
   feedback loops that distort prices away from any theoretical equilibrium). Explain that these
   philosophical principles are the fundamental reason the full Kelly fraction is cut in half –
   to protect the investor against the inherent uncertainty and model error that no quantitative
   framework can fully eliminate.

6. **Supplementary Analysis – Board of Legendary Investors**

   - **Graham's View (Graham Number)**: Compare the Graham Number to the Current Stock Price.
     If the price exceeds the Graham Number, the stock carries a significant premium above its
     hard asset base. If the price is below, it may be undervalued on a classic value basis.

   - **Greenblatt's View (Earnings Yield)**: Analyze whether the Earnings Yield (EBIT / EV)
     offers a strong core return relative to a risk-free benchmark (~4-5%). A high yield
     suggests the business is generating substantial operating profit per dollar of enterprise value.

   - **Marks' Risk Warning (Interest Coverage)**: If the Interest Coverage ratio is below 3.0,
     issue a SEVERE WARNING that the company may struggle to service its debt during economic
     downturns. This is a critical credit risk flag per Howard Marks' distressed-debt philosophy.

   - **Reality Check (Reverse DCF – Implied Growth Rate)**: Explicitly state the Implied Growth
     Rate calculated by the Reverse DCF. Explain to the user exactly what percentage of annual
     FCF growth is already priced into the stock by the market. Objectively assess whether this
     market expectation is realistic, ambitious, or highly speculative based on the company's
     historical earnings growth.

If the stock was REJECTED at any stage:
- Clearly state which mathematical condition failed.
- Explain in plain language what that failure means for the investor.
- If the stock failed due to negative Owner Earnings (FCF), explain that the company is
  burning more cash than it generates from operations and therefore cannot be valued using
  a Discounted Cash Flow model. This is a fundamental red flag.
- Still discuss the remaining stages and supplementary metrics for completeness.

If the stock PASSED all stages:
- Explain the valuation discount, PEGY attractiveness, and recommended portfolio allocation.

Use markdown formatting with headers, bold, and bullet points for readability."""


def _build_user_prompt(
    data: FinancialData,
    s1: Stage1Result,
    s2: Stage2Result,
    s3: Stage3Result,
    s4: Stage4Result | None,
    supp: SupplementaryResult,
    overall_pass: bool,
) -> str:
    lines = [
        f"# Analysis Results for {data.ticker}",
        f"**Current Price:** ${data.current_price:.2f}",
        f"**EPS:** ${data.eps:.2f}",
        f"**Book Value per Share:** ${data.book_value_per_share:.2f}",
        f"**P/E Ratio:** {data.trailing_pe:.2f}",
        f"**Dividend Yield:** {data.dividend_yield * 100:.2f}%",
        f"**Earnings Growth:** {data.earnings_growth * 100:.2f}%",
        f"**EBIT:** ${data.ebit:,.2f}",
        f"**Enterprise Value:** ${data.enterprise_value:,.2f}",
        f"**Interest Expense:** ${data.interest_expense:,.2f}",
        "",
        "## Stage 1 – Financial Quality (Ackman)",
        f"- ROIC values (most recent first): {s1.roic_values}",
        f"- ROIC consistent > 10%: **{'PASS' if s1.roic_consistent else 'FAIL'}**",
        f"- Debt Ratio: {s1.debt_ratio:.4f} (threshold <= 0.25): **{'PASS' if s1.debt_ratio_ok else 'FAIL'}**",
        f"- Stage 1 overall: **{'PASS' if s1.passed else 'FAIL'}**",
        "",
        "## Stage 2 – Intrinsic Value (Buffett)",
        f"- CapEx: ${s2.capex:,.2f}",
        f"- Owner Earnings (FCF): ${s2.owner_earnings:,.2f}",
        f"- DCF Intrinsic Value (total): ${s2.dcf_intrinsic_value:,.2f}",
        f"- Intrinsic Value per Share: ${s2.iv_per_share:.2f}",
        f"- Margin of Safety: {s2.margin_of_safety:.4f} ({s2.margin_of_safety * 100:.2f}%) (threshold >= 30%): **{'PASS' if s2.mos_ok else 'FAIL'}**",
        f"- Stage 2 overall: **{'PASS' if s2.passed else 'FAIL'}**",
        "",
        "## Stage 3 – Growth Premium (Lynch)",
        f"- PEGY Ratio: {s3.pegy:.4f} (threshold <= 1.0): **{'PASS' if s3.pegy_ok else 'FAIL'}**",
        f"- Lynch Fair Value: ${s3.lynch_fair_value:,.2f}",
        f"- Stage 3 overall: **{'PASS' if s3.passed else 'FAIL'}**",
        "",
        "## Stage 4 – Risk Sizing (Kelly / Soros)",
    ]

    if s4:
        lines += [
            f"- Risk/Reward (b) ratio: {s4.b_ratio:.4f}",
            f"- Full Kelly: {s4.full_kelly:.4f} ({s4.full_kelly * 100:.2f}%)",
            f"- **Half-Kelly (recommended allocation): {s4.half_kelly:.4f} ({s4.half_kelly * 100:.2f}%)**",
        ]
    else:
        lines.append("- Stage 4 was NOT computed (prior stages did not all pass).")

    igr_label = (
        f"{supp.implied_growth_rate * 100:.2f}%"
        if supp.implied_growth_rate >= 0
        else "Exceeds 50% (extremely overvalued or negative FCF)"
    )
    lines += [
        "",
        "## Supplementary Metrics – Board of Legendary Investors",
        f"- **Graham Number:** ${supp.graham_number:.2f} (Current Price: ${data.current_price:.2f})",
        f"- **Earnings Yield (Greenblatt):** {supp.earnings_yield * 100:.2f}%",
        f"- **Interest Coverage (Marks):** {supp.interest_coverage:.2f}x"
        + (" ⚠️ BELOW 3.0 – SEVERE RISK" if supp.interest_coverage < 3.0 else ""),
        f"- **Implied Growth Rate (Reverse DCF):** {igr_label}",
        "",
        f"## Overall Verdict: **{'PASS - Investable' if overall_pass else 'REJECT'}**",
    ]

    return "\n".join(lines)


def _fallback_report(user_prompt: str, error_message: str) -> str:
    return (
        f"{error_message}\n\n"
        "---\n\n"
        "## Raw Metrics (fallback display)\n\n"
        f"{user_prompt}"
    )


async def generate_report(
    data: FinancialData,
    s1: Stage1Result,
    s2: Stage2Result,
    s3: Stage3Result,
    s4: Stage4Result | None,
    supp: SupplementaryResult,
    overall_pass: bool,
) -> str:
    user_prompt = _build_user_prompt(data, s1, s2, s3, s4, supp, overall_pass)

    try:
        return await _call_ollama(user_prompt)
    except _OllamaNotRunningError as exc:
        logger.error("Ollama is not running: %s", exc)
        return _fallback_report(
            user_prompt,
            "**Ollama is not running.** Start it with `ollama serve` in a terminal.\n\n"
            "The raw analysis metrics are shown below.",
        )
    except _OllamaModelNotFoundError as exc:
        logger.error("Ollama model not found: %s", exc)
        model = os.getenv("OLLAMA_MODEL", "mistral")
        return _fallback_report(
            user_prompt,
            f"**Ollama model '{model}' is not installed.** "
            f"Run `ollama pull {model}` in a terminal to download it.\n\n"
            "The raw analysis metrics are shown below.",
        )
    except _OllamaTimeoutError as exc:
        logger.warning("Ollama request timed out: %s", exc)
        return _fallback_report(
            user_prompt,
            "**Ollama timed out.** The model may still be loading into memory. "
            "Try again in a few seconds.\n\n"
            "The raw analysis metrics are shown below.",
        )
    except _OllamaEmptyResponseError as exc:
        logger.warning("Ollama returned empty response: %s", exc)
        return _fallback_report(
            user_prompt,
            "**Ollama returned an empty response.** "
            "The model may have failed to generate output. Try again.\n\n"
            "The raw analysis metrics are shown below.",
        )
    except Exception as exc:
        logger.exception("Unexpected Ollama error for %s", data.ticker)
        return _fallback_report(
            user_prompt,
            f"**Unexpected LLM error:** {exc}\n\n"
            "Make sure Ollama is running (`ollama serve`) and the model is installed "
            f"(`ollama pull {os.getenv('OLLAMA_MODEL', 'mistral')}`).",
        )


class _OllamaNotRunningError(Exception):
    """Raised when the Ollama server is unreachable."""


class _OllamaModelNotFoundError(Exception):
    """Raised when the requested model is not pulled in Ollama."""


class _OllamaTimeoutError(Exception):
    """Raised when the Ollama request exceeds the timeout."""


class _OllamaEmptyResponseError(Exception):
    """Raised when Ollama returns a response with no content."""


async def _call_ollama(user_prompt: str) -> str:
    model_name = os.getenv("OLLAMA_MODEL", "mistral")
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{ollama_host}/api/chat",
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                },
            )
    except httpx.ConnectError as exc:
        raise _OllamaNotRunningError(
            f"Cannot connect to Ollama at {ollama_host}: {exc}"
        ) from exc
    except httpx.TimeoutException as exc:
        raise _OllamaTimeoutError(
            f"Ollama request timed out after 120s: {exc}"
        ) from exc

    if resp.status_code == 404:
        raise _OllamaModelNotFoundError(
            f"Model '{model_name}' not found in Ollama (HTTP 404)"
        )

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        error_body = resp.text[:200] if resp.text else "no details"
        raise RuntimeError(
            f"Ollama returned HTTP {resp.status_code}: {error_body}"
        ) from exc

    try:
        data = resp.json()
    except ValueError as exc:
        raise _OllamaEmptyResponseError(
            f"Ollama returned non-JSON response: {resp.text[:200]}"
        ) from exc

    content = data.get("message", {}).get("content", "").strip()
    if not content:
        raise _OllamaEmptyResponseError("Ollama returned an empty message body")

    return content
