"""Model portfolios are complete mixes; return estimates are weighted averages."""

import pytest

from cpb.allocation import (
    ASSET_CLASSES,
    MODEL_PORTFOLIOS,
    TEN_YEAR_RETURNS,
    expected_return,
    expected_volatility,
    model_portfolio,
    valuation_adjustment,
)


class TestModelPortfolios:
    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
    def test_weights_sum_to_one(self, level):
        assert sum(model_portfolio(level).values()) == pytest.approx(1.0)

    @pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
    def test_covers_only_known_asset_classes(self, level):
        assert set(model_portfolio(level)) == set(ASSET_CLASSES)

    def test_equity_share_rises_with_level(self):
        equity = ("us_equity", "intl_equity", "em_equity")
        shares = [
            sum(MODEL_PORTFOLIOS[level][a] for a in equity) for level in range(1, 6)
        ]
        assert shares == sorted(shares)
        assert shares[0] < shares[-1]

    def test_rejects_unknown_level(self):
        with pytest.raises(ValueError, match="risk level"):
            model_portfolio(6)

    def test_returns_a_copy(self):
        mix = model_portfolio(3)
        mix["us_equity"] = 0.99
        assert MODEL_PORTFOLIOS[3]["us_equity"] != 0.99


class TestValuationAdjustment:
    def test_fair_value_means_no_nudge(self):
        assert valuation_adjustment(0.0) == 0.0

    def test_rich_asset_loses_a_tenth_of_the_premium(self):
        assert valuation_adjustment(0.10) == pytest.approx(-0.01)

    def test_cheap_asset_gains_a_tenth_of_the_discount(self):
        assert valuation_adjustment(-0.10) == pytest.approx(0.01)

    def test_nudge_is_capped_at_two_percent(self):
        assert valuation_adjustment(0.50) == pytest.approx(-0.02)
        assert valuation_adjustment(-0.50) == pytest.approx(0.02)


class TestExpectedReturn:
    def test_single_asset_matches_assumption(self):
        assert expected_return({"us_equity": 1.0}) == pytest.approx(
            TEN_YEAR_RETURNS["us_equity"]
        )

    def test_weighted_average_by_hand(self):
        weights = {"us_equity": 0.5, "core_bonds": 0.5}
        expected = 0.5 * 0.065 + 0.5 * 0.040
        assert expected_return(weights) == pytest.approx(expected)

    def test_valuation_premium_lowers_the_estimate(self):
        weights = {"us_equity": 1.0}
        rich = expected_return(weights, valuation_premiums={"us_equity": 0.10})
        assert rich == pytest.approx(TEN_YEAR_RETURNS["us_equity"] - 0.01)

    def test_rejects_weights_not_summing_to_one(self):
        with pytest.raises(ValueError, match="sum to 1"):
            expected_return({"us_equity": 0.5})

    def test_rejects_unknown_asset_class(self):
        with pytest.raises(ValueError, match="asset classes"):
            expected_return({"crypto": 1.0})


class TestExpectedVolatility:
    def test_volatility_rises_with_level(self):
        vols = [expected_volatility(level) for level in range(1, 6)]
        assert vols == sorted(vols)

    def test_rejects_unknown_level(self):
        with pytest.raises(ValueError, match="risk level"):
            expected_volatility(0)
