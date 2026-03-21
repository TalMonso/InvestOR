import pytest

from app.analysis.stage2_buffett import (
    calc_owner_earnings,
    calc_dcf,
    calc_margin_of_safety,
)


class TestOwnerEarnings:
    def test_positive_fcf(self):
        # OCF=10M, CapEx=-3M → OE = 10M - 3M = 7M
        result = calc_owner_earnings(10_000_000, -3_000_000)
        assert result == pytest.approx(7_000_000)

    def test_negative_fcf(self):
        # OCF=2M, CapEx=-5M → OE = 2M - 5M = -3M
        result = calc_owner_earnings(2_000_000, -5_000_000)
        assert result == pytest.approx(-3_000_000)

    def test_zero_ocf(self):
        result = calc_owner_earnings(0, -1_000_000)
        assert result == pytest.approx(-1_000_000)

    def test_zero_capex(self):
        result = calc_owner_earnings(5_000_000, 0)
        assert result == pytest.approx(5_000_000)


class TestDCF:
    def test_positive_earnings(self):
        result = calc_dcf(1_000_000, 0.10)
        assert result > 0

    def test_zero_earnings(self):
        assert calc_dcf(0, 0.10) == 0.0

    def test_negative_earnings(self):
        assert calc_dcf(-100, 0.10) == 0.0

    def test_higher_growth_gives_higher_value(self):
        low = calc_dcf(1_000_000, 0.05)
        high = calc_dcf(1_000_000, 0.15)
        assert high > low

    def test_growth_capped_at_15_percent(self):
        capped = calc_dcf(1_000_000, 0.50)
        at_cap = calc_dcf(1_000_000, 0.15)
        assert capped == pytest.approx(at_cap)

    def test_uses_terminal_growth_not_multiple(self):
        result = calc_dcf(1_000_000, 0.10, discount_rate=0.10, years=5, terminal_growth=0.025)
        assert result > 0


class TestMarginOfSafety:
    def test_positive_mos(self):
        assert calc_margin_of_safety(200, 100) == pytest.approx(0.50)

    def test_zero_mos(self):
        assert calc_margin_of_safety(100, 100) == pytest.approx(0.0)

    def test_negative_mos(self):
        result = calc_margin_of_safety(80, 100)
        assert result < 0

    def test_zero_iv(self):
        assert calc_margin_of_safety(0, 100) == -1.0

    def test_exactly_30_percent(self):
        assert calc_margin_of_safety(100, 70) == pytest.approx(0.30)


class TestEvaluateNegativeOE:
    def test_negative_oe_short_circuits(self):
        from app.analysis.stage2_buffett import evaluate
        from app.models.schemas import FinancialData

        data = FinancialData(
            ticker="TEST",
            current_price=100.0,
            shares_outstanding=1_000_000,
            trailing_pe=15.0,
            dividend_yield=0.02,
            earnings_growth=0.10,
            eps=5.0,
            operating_cash_flow=[2_000_000],
            capital_expenditure=[-5_000_000],
        )
        result = evaluate(data)
        assert result.passed is False
        assert result.owner_earnings < 0
        assert result.iv_per_share == 0.0
        assert result.margin_of_safety == -1.0
