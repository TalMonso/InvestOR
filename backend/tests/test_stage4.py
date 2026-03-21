import pytest

from app.analysis.stage4_kelly import calc_b_ratio, calc_kelly, calc_half_kelly


class TestBRatio:
    def test_basic(self):
        # (200 - 100) / (100 * 0.50) = 100 / 50 = 2.0
        result = calc_b_ratio(200, 100)
        assert result == pytest.approx(2.0)

    def test_overvalued_stock(self):
        # (80 - 100) / (100 * 0.50) = -20 / 50 = -0.4
        result = calc_b_ratio(80, 100)
        assert result == pytest.approx(-0.4)

    def test_zero_price(self):
        result = calc_b_ratio(100, 0)
        assert result == 0.0


class TestKelly:
    def test_favorable_bet(self):
        # K = 0.60 - (0.40 / 2.0) = 0.60 - 0.20 = 0.40
        result = calc_kelly(0.60, 2.0)
        assert result == pytest.approx(0.40)

    def test_negative_b_returns_zero(self):
        assert calc_kelly(0.60, -1.0) == 0.0

    def test_zero_b_returns_zero(self):
        assert calc_kelly(0.60, 0.0) == 0.0

    def test_b_equals_one(self):
        # K = 0.60 - 0.40/1.0 = 0.20
        result = calc_kelly(0.60, 1.0)
        assert result == pytest.approx(0.20)


class TestHalfKelly:
    def test_capped_at_20_percent(self):
        # 0.52 / 2 = 0.26, but capped at MAX_ALLOCATION (0.20)
        assert calc_half_kelly(0.52) == pytest.approx(0.20)

    def test_under_cap(self):
        # 0.30 / 2 = 0.15, under the 0.20 cap
        assert calc_half_kelly(0.30) == pytest.approx(0.15)

    def test_negative_kelly_floors_to_zero(self):
        assert calc_half_kelly(-0.10) == 0.0

    def test_zero(self):
        assert calc_half_kelly(0.0) == 0.0
