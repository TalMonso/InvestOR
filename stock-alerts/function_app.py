"""Azure Function – Weekly Stock Alert Bot (Model V2, Timer Trigger).

Every Tuesday at 20:00 UTC, fetches weekly price changes for a watchlist
of tickers and sends a Telegram alert if any moved >= 5%.
"""

import json
import logging
import os
import urllib.request
from datetime import datetime, timezone

import azure.functions as func
import yfinance as yf

app = func.FunctionApp()

WATCHLIST = ["NVDA", "MSFT", "GOOGL", "WIX", "AMZN", "META", "AAPL", "ORCL", "AMD"]
THRESHOLD_PCT = 5.0
TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def fetch_weekly_change(ticker: str) -> dict | None:
    """Download ~10 days of daily closes and compute the 7-day % change.

    Returns a dict with ticker, prices, and pct_change, or None on failure.
    """
    try:
        df = yf.download(ticker, period="10d", interval="1d", progress=False)
        if df is None or df.empty or len(df) < 2:
            logging.warning("Not enough data for %s", ticker)
            return None

        close = df["Close"]
        if hasattr(close, "columns"):
            close = close.iloc[:, 0]

        today_close = float(close.iloc[-1])
        week_ago_close = float(close.iloc[0])

        if week_ago_close == 0:
            return None

        pct_change = ((today_close - week_ago_close) / week_ago_close) * 100

        return {
            "ticker": ticker,
            "today": round(today_close, 2),
            "week_ago": round(week_ago_close, 2),
            "pct_change": round(pct_change, 2),
        }
    except Exception as exc:
        logging.error("Failed to fetch %s: %s", ticker, exc)
        return None


def build_message(alerts: list[dict]) -> str:
    """Format the alert list into a Telegram-friendly message."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"🚨 *Weekly Stock Alert* — {now}\n"]

    for a in alerts:
        emoji = "📈" if a["pct_change"] > 0 else "📉"
        direction = "UP" if a["pct_change"] > 0 else "DOWN"
        lines.append(
            f"{emoji} *{a['ticker']}* {direction} *{abs(a['pct_change']):.2f}%*\n"
            f"    ${a['week_ago']:.2f} → ${a['today']:.2f}"
        )

    lines.append(f"\n📊 {len(alerts)} stock(s) moved ≥ {THRESHOLD_PCT}% this week.")
    return "\n".join(lines)


def send_telegram(message: str) -> None:
    """POST the message to Telegram using only stdlib urllib."""
    token = os.environ.get("TELEGRAM_TOKEN", "")
    chat_id = os.environ.get("CHAT_ID", "")

    if not token or not chat_id:
        logging.error("TELEGRAM_TOKEN or CHAT_ID not set — skipping send.")
        return

    url = TELEGRAM_API.format(token=token)
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            logging.info("Telegram response: %s", resp.status)
    except Exception as exc:
        logging.error("Failed to send Telegram message: %s", exc)


@app.timer_trigger(
    schedule="0 0 20 * * 2",
    arg_name="myTimer",
    run_on_startup=False,
)
def stock_alert_timer(myTimer: func.TimerRequest) -> None:
    """Runs every Tuesday at 20:00 UTC. Checks watchlist for ≥5% weekly moves."""
    logging.info("Stock alert function triggered at %s", datetime.utcnow())

    alerts: list[dict] = []
    for ticker in WATCHLIST:
        result = fetch_weekly_change(ticker)
        if result and abs(result["pct_change"]) >= THRESHOLD_PCT:
            alerts.append(result)
            logging.info("ALERT: %s moved %.2f%%", ticker, result["pct_change"])

    if alerts:
        message = build_message(alerts)
        send_telegram(message)
        logging.info("Sent alert for %d stock(s).", len(alerts))
    else:
        logging.info("No stocks exceeded the %.1f%% threshold. No alert sent.", THRESHOLD_PCT)
