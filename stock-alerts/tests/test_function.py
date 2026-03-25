"""Tests for the stock-alerts Azure Function.

Unit tests: fully mocked (no network).
Integration test: marked with @pytest.mark.integration (real yfinance call).
"""

import json
from unittest.mock import patch, MagicMock

import pandas as pd
import pytest

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from function_app import (
    fetch_weekly_change,
    build_message,
    send_telegram,
    THRESHOLD_PCT,
)


# ---------------------------------------------------------------------------
# Helpers – build a fake yfinance DataFrame
# ---------------------------------------------------------------------------

def _make_price_df(start_price: float, end_price: float, days: int = 8) -> pd.DataFrame:
    """Create a DataFrame that mimics yfinance output with linearly interpolated closes."""
    prices = [
        start_price + (end_price - start_price) * i / (days - 1)
        for i in range(days)
    ]
    dates = pd.bdate_range(end=pd.Timestamp.today(), periods=days)
    return pd.DataFrame({"Close": prices}, index=dates)


# ---------------------------------------------------------------------------
# Unit tests – fetch_weekly_change
# ---------------------------------------------------------------------------

class TestFetchWeeklyChange:
    @patch("function_app.yf.download")
    def test_alert_triggered_on_5pct_up(self, mock_download):
        """A +6% rise should produce a result with pct_change ~ +6."""
        mock_download.return_value = _make_price_df(100.0, 106.0)
        result = fetch_weekly_change("FAKE")
        assert result is not None
        assert result["pct_change"] == pytest.approx(6.0, abs=0.5)
        assert result["ticker"] == "FAKE"

    @patch("function_app.yf.download")
    def test_alert_triggered_on_5pct_down(self, mock_download):
        """A -7% drop should produce a result with pct_change ~ -7."""
        mock_download.return_value = _make_price_df(100.0, 93.0)
        result = fetch_weekly_change("FAKE")
        assert result is not None
        assert result["pct_change"] == pytest.approx(-7.0, abs=0.5)

    @patch("function_app.yf.download")
    def test_no_alert_below_threshold(self, mock_download):
        """A +3% move is under the 5% threshold — function still returns data,
        but the caller should not add it to alerts."""
        mock_download.return_value = _make_price_df(100.0, 103.0)
        result = fetch_weekly_change("FAKE")
        assert result is not None
        assert abs(result["pct_change"]) < THRESHOLD_PCT

    @patch("function_app.yf.download")
    def test_empty_dataframe_returns_none(self, mock_download):
        mock_download.return_value = pd.DataFrame()
        result = fetch_weekly_change("FAKE")
        assert result is None

    @patch("function_app.yf.download")
    def test_exception_returns_none(self, mock_download):
        mock_download.side_effect = Exception("network error")
        result = fetch_weekly_change("FAKE")
        assert result is None


# ---------------------------------------------------------------------------
# Unit tests – build_message
# ---------------------------------------------------------------------------

class TestBuildMessage:
    def test_up_emoji_present(self):
        alerts = [{"ticker": "NVDA", "today": 130.0, "week_ago": 120.0, "pct_change": 8.33}]
        msg = build_message(alerts)
        assert "📈" in msg
        assert "NVDA" in msg
        assert "8.33%" in msg

    def test_down_emoji_present(self):
        alerts = [{"ticker": "AMD", "today": 90.0, "week_ago": 100.0, "pct_change": -10.0}]
        msg = build_message(alerts)
        assert "📉" in msg
        assert "AMD" in msg
        assert "10.00%" in msg

    def test_multiple_alerts(self):
        alerts = [
            {"ticker": "NVDA", "today": 130.0, "week_ago": 120.0, "pct_change": 8.33},
            {"ticker": "AMD", "today": 90.0, "week_ago": 100.0, "pct_change": -10.0},
        ]
        msg = build_message(alerts)
        assert "2 stock(s)" in msg


# ---------------------------------------------------------------------------
# Unit tests – send_telegram
# ---------------------------------------------------------------------------

class TestSendTelegram:
    @patch.dict(os.environ, {"TELEGRAM_TOKEN": "fake-token", "CHAT_ID": "12345"})
    @patch("function_app.urllib.request.urlopen")
    def test_sends_correct_request(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        send_telegram("Test message")

        mock_urlopen.assert_called_once()
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        assert "fake-token" in req.full_url
        body = json.loads(req.data.decode("utf-8"))
        assert body["chat_id"] == "12345"
        assert body["text"] == "Test message"
        assert body["parse_mode"] == "Markdown"

    @patch.dict(os.environ, {"TELEGRAM_TOKEN": "", "CHAT_ID": ""})
    @patch("function_app.urllib.request.urlopen")
    def test_skips_when_no_credentials(self, mock_urlopen):
        send_telegram("Test message")
        mock_urlopen.assert_not_called()


# ---------------------------------------------------------------------------
# Integration test – real yfinance call (opt-in)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_aapl_data_is_valid():
    """Fetches real AAPL data from Yahoo Finance and validates the response."""
    import yfinance as yf

    df = yf.download("AAPL", period="10d", interval="1d", progress=False)
    assert df is not None
    assert not df.empty
    assert "Close" in df.columns
    assert len(df) >= 2
