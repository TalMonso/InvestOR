import pytest

from app.analysis.stage1_ackman import calc_roic, check_roic_consistency, calc_debt_ratio
from app.models.schemas import FinancialData


def _make_data(**overrides) -> FinancialData:
    defaults = dict(
        ticker="TEST",
        current_price=100.0,
        shares_outstanding=1_000_000,
        trailing_pe=15.0,
        dividend_yield=0.02,
        earnings_growth=0.10,
        eps=6.67,
        net_income=[500_000, 450_000, 400_000, 350_000],
        total_revenue=[5_000_000, 4_800_000, 4_500_000, 4_000_000],
        depreciation_amortization=[100_000, 90_000, 80_000, 70_000],
        dividends_paid=[-50_000, -45_000, -40_000, -35_000],
        total_equity=[2_000_000, 1_900_000, 1_800_000, 1_700_000],
        total_debt=[500_000, 480_000, 460_000, 440_000],
        cash=[200_000, 190_000, 180_000, 170_000],
        total_liabilities=[600_000, 580_000, 560_000, 540_000],
        total_assets=[3_000_000, 2_900_000, 2_800_000, 2_700_000],
        net_ppe=[1_000_000, 950_000, 900_000, 850_000],
        capital_expenditure=[-150_000, -140_000, -130_000, -120_000],
    )
    defaults.update(overrides)
    return FinancialData(**defaults)


class TestCalcROIC:
    def test_basic(self):
        # (500_000 - 50_000) / (2_000_000 + 500_000 - 200_000)
        # = 450_000 / 2_300_000 ≈ 0.19565
        result = calc_roic(500_000, -50_000, 2_000_000, 500_000, 200_000)
        assert result == pytest.approx(0.19565, rel=1e-3)

    def test_zero_invested_capital(self):
        result = calc_roic(100_000, 0, 0, 0, 100)
        assert result == 0.0

    def test_negative_dividends_treated_as_positive(self):
        r1 = calc_roic(500_000, -50_000, 2_000_000, 500_000, 200_000)
        r2 = calc_roic(500_000, 50_000, 2_000_000, 500_000, 200_000)
        assert r1 == pytest.approx(r2)


class TestROICConsistency:
    def test_all_above_threshold(self):
        assert check_roic_consistency([0.15, 0.12, 0.11]) is True

    def test_one_below_threshold(self):
        assert check_roic_consistency([0.15, 0.09, 0.11]) is False

    def test_exactly_at_threshold_fails(self):
        assert check_roic_consistency([0.10]) is False

    def test_empty_list(self):
        assert check_roic_consistency([]) is False


class TestDebtRatio:
    def test_basic(self):
        assert calc_debt_ratio(600_000, 3_000_000) == pytest.approx(0.2)

    def test_exactly_at_threshold(self):
        assert calc_debt_ratio(250_000, 1_000_000) == pytest.approx(0.25)

    def test_zero_assets(self):
        assert calc_debt_ratio(100_000, 0) == 1.0


class TestStage1Evaluate:
    def test_pass(self):
        from app.analysis.stage1_ackman import evaluate

        data = _make_data()
        result = evaluate(data)
        assert result.passed is True
        assert result.roic_consistent is True
        assert result.debt_ratio_ok is True

    def test_fail_high_debt(self):
        from app.analysis.stage1_ackman import evaluate

        data = _make_data(
            total_liabilities=[2_000_000, 1_900_000, 1_800_000, 1_700_000]
        )
        result = evaluate(data)
        assert result.debt_ratio_ok is False
        assert result.passed is False
