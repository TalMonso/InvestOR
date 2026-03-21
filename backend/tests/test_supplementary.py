import math

import pytest

from app.analysis.supplementary import (
    calc_graham_number,
    calc_earnings_yield,
    calc_interest_coverage,
    calc_implied_growth_rate,
)


class TestGrahamNumber:
    def test_basic(self):
        # sqrt(22.5 * 5 * 40) = sqrt(4500) ≈ 67.08
        result = calc_graham_number(5.0, 40.0)
        assert result == pytest.approx(math.sqrt(4500), rel=1e-3)

    def test_negative_eps(self):
        assert calc_graham_number(-3.0, 40.0) == 0.0

    def test_negative_bvps(self):
        assert calc_graham_number(5.0, -10.0) == 0.0

    def test_both_negative(self):
        assert calc_graham_number(-2.0, -5.0) == 0.0

    def test_zero_eps(self):
        assert calc_graham_number(0.0, 40.0) == 0.0

    def test_zero_bvps(self):
        assert calc_graham_number(5.0, 0.0) == 0.0


class TestEarningsYield:
    def test_basic(self):
        # 10B EBIT / 100B EV = 0.10
        result = calc_earnings_yield(10e9, 100e9)
        assert result == pytest.approx(0.10)

    def test_zero_ev(self):
        assert calc_earnings_yield(10e9, 0.0) == 0.0

    def test_negative_ev(self):
        assert calc_earnings_yield(10e9, -5e9) == 0.0

    def test_negative_ebit(self):
        result = calc_earnings_yield(-2e9, 50e9)
        assert result == pytest.approx(-0.04)

    def test_zero_ebit(self):
        assert calc_earnings_yield(0.0, 50e9) == pytest.approx(0.0)


class TestInterestCoverage:
    def test_basic(self):
        # 10B EBIT / 2B interest = 5.0
        result = calc_interest_coverage(10e9, 2e9)
        assert result == pytest.approx(5.0)

    def test_zero_interest(self):
        result = calc_interest_coverage(10e9, 0.0)
        assert result == 999.99

    def test_zero_interest_zero_ebit(self):
        result = calc_interest_coverage(0.0, 0.0)
        assert result == 0.0

    def test_negative_ebit(self):
        result = calc_interest_coverage(-5e9, 2e9)
        assert result < 0

    def test_below_three_is_dangerous(self):
        result = calc_interest_coverage(2e9, 1e9)
        assert result == pytest.approx(2.0)
        assert result < 3.0

    def test_capped_at_999(self):
        result = calc_interest_coverage(100e9, 0.001)
        assert result == 999.99


class TestImpliedGrowthRate:
    def test_positive_fcf(self):
        result = calc_implied_growth_rate(
            fcf=5e9,
            current_price=150.0,
            shares_outstanding=1e9,
        )
        assert result >= 0
        assert result <= 0.50

    def test_negative_fcf(self):
        result = calc_implied_growth_rate(
            fcf=-1e9,
            current_price=100.0,
            shares_outstanding=1e9,
        )
        assert result == 0.0

    def test_zero_fcf(self):
        result = calc_implied_growth_rate(
            fcf=0.0,
            current_price=100.0,
            shares_outstanding=1e9,
        )
        assert result == 0.0

    def test_zero_price(self):
        result = calc_implied_growth_rate(
            fcf=5e9,
            current_price=0.0,
            shares_outstanding=1e9,
        )
        assert result == 0.0

    def test_very_cheap_stock_low_growth(self):
        result = calc_implied_growth_rate(
            fcf=10e9,
            current_price=5.0,
            shares_outstanding=1e9,
        )
        assert result >= 0
        assert result <= 0.10

    def test_extremely_overvalued_returns_negative(self):
        result = calc_implied_growth_rate(
            fcf=100_000,
            current_price=10_000.0,
            shares_outstanding=1e9,
        )
        assert result == -1.0
