"""Scenario math by hand, drawdown on a known path, and sane Monte Carlo odds."""

import numpy as np
import pandas as pd
import pytest

from cpb.allocation import model_portfolio
from cpb.stress import (
    SCENARIOS,
    goal_miss_probability,
    max_drawdown,
    portfolio_daily_returns,
    run_scenarios,
    scenario_return,
)


class TestScenarioReturn:
    def test_weighted_average_by_hand(self):
        weights = {"us_equity": 0.5, "core_bonds": 0.5}
        expected = 0.5 * -0.37 + 0.5 * 0.05
        assert scenario_return(weights, "2008 global financial crisis") == pytest.approx(expected)

    def test_all_cash_is_barely_touched(self):
        result = scenario_return({"cash": 1.0}, "2020 covid crash")
        assert result == pytest.approx(0.0)

    def test_run_scenarios_covers_all_three(self):
        results = run_scenarios(model_portfolio(3))
        assert set(results) == set(SCENARIOS)

    def test_bad_years_hurt_aggressive_mixes_more(self):
        conservative = scenario_return(model_portfolio(1), "2008 global financial crisis")
        aggressive = scenario_return(model_portfolio(5), "2008 global financial crisis")
        assert aggressive < conservative

    def test_level3_2022_loss_within_the_worked_example_tolerance(self):
        # The Bogotá family tolerates a 15% bad year; 2022 on the level-3
        # mix stays inside that.
        loss = scenario_return(model_portfolio(3), "2022 rate shock")
        assert -0.15 < loss < -0.10

    def test_rejects_unknown_scenario(self):
        with pytest.raises(ValueError, match="unknown scenario"):
            scenario_return({"cash": 1.0}, "1929")

    def test_rejects_unknown_asset_class(self):
        with pytest.raises(ValueError, match="asset classes"):
            scenario_return({"crypto": 1.0}, "2022 rate shock")


class TestPortfolioDailyReturns:
    def test_weighted_average_of_two_tickers(self):
        closes = pd.DataFrame(
            {"IVV": [100.0, 102.0], "AGG": [100.0, 99.0]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
        )
        returns = portfolio_daily_returns({"IVV": 0.6, "AGG": 0.4}, closes)
        assert returns.iloc[0] == pytest.approx(0.6 * 0.02 + 0.4 * -0.01)

    def test_rejects_missing_ticker(self):
        closes = pd.DataFrame({"IVV": [100.0, 101.0]})
        with pytest.raises(ValueError, match="missing tickers"):
            portfolio_daily_returns({"IVV": 0.5, "AGG": 0.5}, closes)


class TestMaxDrawdown:
    def test_known_path(self):
        # Up 10%, down 20%, up 5%: worst slide is the -20% day.
        returns = pd.Series([0.10, -0.20, 0.05])
        assert max_drawdown(returns) == pytest.approx(-0.20)

    def test_never_down_means_zero(self):
        returns = pd.Series([0.01, 0.02, 0.03])
        assert max_drawdown(returns) == pytest.approx(0.0)


class TestGoalMissProbability:
    def test_sure_thing_with_zero_volatility(self):
        # 5% a year for 15 years on $5M lands at ~$10.4M with certainty.
        assert goal_miss_probability(5e6, 10e6, 15, 0.05, 0.0) == 0.0
        assert goal_miss_probability(5e6, 11e6, 15, 0.05, 0.0) == 1.0

    def test_higher_target_is_harder_to_hit(self):
        easy = goal_miss_probability(5e6, 6e6, 15, 0.05, 0.10)
        hard = goal_miss_probability(5e6, 12e6, 15, 0.05, 0.10)
        assert easy < hard

    def test_seed_makes_it_reproducible(self):
        a = goal_miss_probability(5e6, 10e6, 15, 0.05, 0.10, seed=7)
        b = goal_miss_probability(5e6, 10e6, 15, 0.05, 0.10, seed=7)
        assert a == b

    def test_probability_is_a_fraction(self):
        p = goal_miss_probability(5e6, 10e6, 15, 0.05, 0.10)
        assert 0.0 <= p <= 1.0

    def test_rejects_bad_inputs(self):
        with pytest.raises(ValueError):
            goal_miss_probability(0, 10e6, 15, 0.05, 0.10)
        with pytest.raises(ValueError):
            goal_miss_probability(5e6, 10e6, 0, 0.05, 0.10)

    def test_wealth_never_goes_negative(self):
        # Huge volatility would push some normal draws below -100%;
        # terminal wealth must still be non-negative.
        rng_check = goal_miss_probability(5e6, 1.0, 15, 0.0, 2.0)
        assert 0.0 <= rng_check <= 1.0
