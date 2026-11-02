"""Currency rules: custody split, rate-difference drift, depreciation hit."""

import pytest

from cpb.fx import (
    custody_split,
    expected_depreciation,
    fx_stress,
    usd_return_of_local_asset,
)


class TestCustodySplit:
    def test_worked_example_split(self):
        split = custody_split(5_000_000, offshore_share=0.60)
        assert split == {"offshore_usd": 3_000_000, "onshore_usd": 2_000_000}

    def test_parts_sum_to_total(self):
        split = custody_split(1_234_567.89, offshore_share=0.37)
        assert split["offshore_usd"] + split["onshore_usd"] == pytest.approx(1_234_567.89)

    def test_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            custody_split(0, 0.5)
        with pytest.raises(ValueError):
            custody_split(1_000_000, 1.5)


class TestExpectedDepreciation:
    def test_rate_difference(self):
        # COP rates at 9% against 4% USD rates → ~5% expected slide a year.
        assert expected_depreciation(0.09, 0.04) == pytest.approx(0.05)

    def test_lower_local_rates_mean_expected_strength(self):
        assert expected_depreciation(0.02, 0.04) == pytest.approx(-0.02)


class TestUsdReturnOfLocalAsset:
    def test_local_return_minus_expected_slide(self):
        # A 10% COP return with a 5% expected slide is worth ~5% in USD.
        assert usd_return_of_local_asset(0.10, 0.09, 0.04) == pytest.approx(0.05)


class TestFxStress:
    def test_worked_example_hit(self):
        # 40% onshore and a 20% COP drop → the portfolio loses ~8% in USD.
        assert fx_stress(0.40, 0.20) == pytest.approx(-0.08)

    def test_no_onshore_means_no_hit(self):
        assert fx_stress(0.0, 0.50) == 0.0

    def test_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            fx_stress(1.2, 0.2)
        with pytest.raises(ValueError):
            fx_stress(0.4, -0.1)

