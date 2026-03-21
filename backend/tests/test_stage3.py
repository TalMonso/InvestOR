import pytest

from app.analysis.stage3_lynch import calc_pegy, calc_lynch_fair_value


class TestPEGY:
    def test_basic(self):
        # PE=15, Growth=15 (whole), DivYield=2 (whole)
        # 15 / (15 + 2) = 0.8824
        result = calc_pegy(15, 15, 2)
        assert result == pytest.approx(0.8824, rel=1e-3)

    def test_high_pe_fails(self):
        # PE=30, Growth=10, DivYield=1 → 30/11 = 2.727
        result = calc_pegy(30, 10, 1)
        assert result > 1.0

    def test_zero_denominator(self):
        result = calc_pegy(15, 0, 0)
        assert result == float("inf")

    def test_exactly_one(self):
        # PE=17, Growth=15, DivYield=2 → 17/17 = 1.0
        result = calc_pegy(17, 15, 2)
        assert result == pytest.approx(1.0)


class TestLynchFairValue:
    def test_basic(self):
        # EPS=5, Growth=15 (whole number) → 5 * 15 = 75
        result = calc_lynch_fair_value(5, 15)
        assert result == pytest.approx(75)

    def test_example_from_spec(self):
        # EPS=4.90, Growth=95.6 → 4.90 * 95.6 = 468.44
        result = calc_lynch_fair_value(4.90, 95.6)
        assert result == pytest.approx(468.44)

    def test_zero_growth(self):
        assert calc_lynch_fair_value(5, 0) == 0.0

    def test_negative_eps_returns_zero(self):
        result = calc_lynch_fair_value(-2, 10)
        assert result == 0.0
