"""The risk level is the most conservative of tolerance, horizon, and goal."""

import pytest

from cpb.profile import (
    ClientProfile,
    goal_level,
    horizon_level,
    ToleranceWarning,
    fits_tolerance,
    loss_tolerance_level,
    risk_level,
    worst_year_loss,
)


def make_profile(**overrides):
    base = dict(
        name="Test client",
        total_assets_usd=1_000_000,
        horizon_years=10,
        goal="balanced",
        max_annual_loss=0.10,
    )
    base.update(overrides)
    return ClientProfile(**base)


class TestLossToleranceLevel:
    def test_highest_level_whose_worst_year_fits(self):
        # Tolerating exactly a level's worst year is enough to hold it.
        assert loss_tolerance_level(0.09) == 1
        assert loss_tolerance_level(0.12) == 2
        assert loss_tolerance_level(0.21) == 3
        assert loss_tolerance_level(0.30) == 4
        assert loss_tolerance_level(0.38) == 5
        assert loss_tolerance_level(0.50) == 5

    def test_between_levels_rounds_down(self):
        # 15% covers level 2's worst year (12%) but not level 3's (21%).
        assert loss_tolerance_level(0.15) == 2
        assert loss_tolerance_level(0.209) == 2

    def test_tolerance_below_every_level_is_level_one_with_a_warning(self):
        with pytest.warns(ToleranceWarning, match="no model portfolio fits a 5%"):
            assert loss_tolerance_level(0.05) == 1
        assert not fits_tolerance(0.05)
        assert fits_tolerance(0.09)


class TestHorizonLevel:
    def test_bands(self):
        assert horizon_level(1) == 1
        assert horizon_level(3) == 2
        assert horizon_level(5) == 3
        assert horizon_level(10) == 4
        assert horizon_level(15) == 5
        assert horizon_level(30) == 5


class TestGoalLevel:
    def test_each_goal(self):
        assert goal_level("preserve") == 2
        assert goal_level("income") == 3
        assert goal_level("balanced") == 4
        assert goal_level("grow") == 5


class TestRiskLevel:
    def test_most_conservative_input_wins(self):
        # Long horizon and a grow goal, but tolerance binds at level 2.
        profile = make_profile(goal="grow", horizon_years=20, max_annual_loss=0.15)
        assert risk_level(profile) == 2

    def test_short_horizon_binds(self):
        profile = make_profile(goal="grow", horizon_years=2, max_annual_loss=0.50)
        assert risk_level(profile) == 1

    def test_preserve_goal_binds(self):
        profile = make_profile(goal="preserve", horizon_years=20, max_annual_loss=0.50)
        assert risk_level(profile) == 2

    def test_worked_example_bogota_family(self):
        # $5M, 15-year horizon, goal grow, tolerates a 15% bad year.
        profile = ClientProfile(
            name="Bogotá family",
            total_assets_usd=5_000_000,
            horizon_years=15,
            goal="grow",
            max_annual_loss=0.15,
            offshore_share=0.60,
            local_currency="COP",
        )
        assert risk_level(profile) == 2
        assert profile.onshore_share == pytest.approx(0.40)


class TestValidation:
    def test_rejects_unknown_goal(self):
        with pytest.raises(ValueError, match="goal"):
            make_profile(goal="moonshot")

    def test_rejects_nonpositive_assets(self):
        with pytest.raises(ValueError, match="total_assets_usd"):
            make_profile(total_assets_usd=0)

    def test_rejects_nonpositive_horizon(self):
        with pytest.raises(ValueError, match="horizon_years"):
            make_profile(horizon_years=0)

    def test_rejects_loss_tolerance_out_of_range(self):
        with pytest.raises(ValueError, match="max_annual_loss"):
            make_profile(max_annual_loss=0.0)
        with pytest.raises(ValueError, match="max_annual_loss"):
            make_profile(max_annual_loss=1.5)

    def test_rejects_offshore_share_out_of_range(self):
        with pytest.raises(ValueError, match="offshore_share"):
            make_profile(offshore_share=1.2)


class TestWorstYearLoss:
    def test_rises_with_level(self):
        losses = [worst_year_loss(level) for level in range(1, 6)]
        assert losses == [0.09, 0.12, 0.21, 0.30, 0.38]
        assert losses == sorted(losses)

    def test_round_trips_with_loss_tolerance_level(self):
        for level in range(1, 6):
            assert loss_tolerance_level(worst_year_loss(level)) == level

    def test_rejects_unknown_level(self):
        with pytest.raises(ValueError, match="risk level"):
            worst_year_loss(0)
