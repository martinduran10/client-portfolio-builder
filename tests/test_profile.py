"""The risk level is the most conservative of tolerance, horizon, and goal."""

import pytest

from cpb.profile import (
    ClientProfile,
    goal_level,
    horizon_level,
    loss_tolerance_level,
    risk_level,
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
    def test_band_edges_are_inclusive(self):
        assert loss_tolerance_level(0.05) == 1
        assert loss_tolerance_level(0.10) == 2
        assert loss_tolerance_level(0.15) == 3
        assert loss_tolerance_level(0.25) == 4
        assert loss_tolerance_level(0.26) == 5

    def test_tiny_tolerance_is_level_one(self):
        assert loss_tolerance_level(0.01) == 1


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
        # Long horizon and a grow goal, but tolerance binds at level 3.
        profile = make_profile(goal="grow", horizon_years=20, max_annual_loss=0.15)
        assert risk_level(profile) == 3

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
        assert risk_level(profile) == 3
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
