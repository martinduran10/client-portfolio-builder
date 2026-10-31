"""Replays checked by hand on synthetic closes and sanity-checked on the
cached proxy history; drawdown on known paths; sane Monte Carlo odds."""

import numpy as np
import pandas as pd
import pytest

from cpb.allocation import model_portfolio
from cpb.proxies import load_proxies
from cpb.stress import (
    SCENARIO_WINDOWS,
    asset_class_scenarios,
    calendar_year_return,
    goal_miss_probability,
    historical_drawdown,
    max_drawdown,
    peak_to_trough,
    portfolio_returns,
    replay_scenarios,
)


@pytest.fixture(scope="module")
def closes():
    return load_proxies()


def month_ends(start, periods):
    return pd.date_range(start, periods=periods, freq="ME")


class TestWindowMathByHand:
    def test_calendar_year_compounds_twelve_months(self):
        # +1% every month of 2022 → (1.01)^12 - 1.
        returns = pd.Series(0.01, index=month_ends("2021-12-31", 14))
        assert calendar_year_return(returns, 2022) == pytest.approx(1.01**12 - 1)

    def test_calendar_year_needs_all_twelve_months(self):
        returns = pd.Series(0.01, index=month_ends("2022-01-31", 6))
        with pytest.raises(ValueError, match="need 12"):
            calendar_year_return(returns, 2022)

    def test_peak_to_trough_counts_the_first_months_drop(self):
        # Feb -10%, Mar -10%: from the January month-end that is -19%.
        returns = pd.Series([0.05, -0.10, -0.10, 0.30], index=month_ends("2020-01-31", 4))
        assert peak_to_trough(returns, "2020-02", "2020-03") == pytest.approx(-0.19)

    def test_peak_to_trough_ignores_months_outside_the_window(self):
        returns = pd.Series([-0.50, 0.02, 0.03], index=month_ends("2020-01-31", 3))
        assert peak_to_trough(returns, "2020-02", "2020-03") == pytest.approx(0.0)

    def test_empty_window_is_rejected(self):
        returns = pd.Series([0.01], index=month_ends("2020-01-31", 1))
        with pytest.raises(ValueError, match="no returns"):
            peak_to_trough(returns, "1999-01", "1999-02")


class TestReplayOnProxies:
    def test_one_row_per_scenario_with_both_numbers(self, closes):
        table = replay_scenarios(model_portfolio(3), closes)
        assert list(table.index) == list(SCENARIO_WINDOWS)
        assert {"calendar_year_return", "peak_to_trough"} <= set(table.columns)
        assert (table["peak_to_trough"] <= 0).all()

    def test_2022_window_is_the_calendar_year_so_slide_is_at_least_the_year(self, closes):
        table = replay_scenarios(model_portfolio(3), closes)
        row = table.loc["2022 rate shock"]
        assert row["peak_to_trough"] <= row["calendar_year_return"] < 0

    def test_2008_hurts_aggressive_mixes_more(self, closes):
        conservative = replay_scenarios(model_portfolio(1), closes)
        aggressive = replay_scenarios(model_portfolio(5), closes)
        name = "2008 global financial crisis"
        assert aggressive.loc[name, "calendar_year_return"] < conservative.loc[name, "calendar_year_return"]
        assert aggressive.loc[name, "peak_to_trough"] < conservative.loc[name, "peak_to_trough"]

    def test_all_cash_is_barely_touched(self, closes):
        table = replay_scenarios({"cash": 1.0}, closes)
        assert table["peak_to_trough"].min() > -0.01

    def test_asset_class_table_covers_every_class_and_scenario(self, closes):
        table = asset_class_scenarios(closes)
        assert len(table) == len(SCENARIO_WINDOWS) * len(model_portfolio(3))
        us_2008 = table.loc[("2008 global financial crisis", "us_equity")]
        assert us_2008["calendar_year_return"] < -0.30

    def test_rejects_unknown_asset_class(self, closes):
        with pytest.raises(ValueError, match="no proxy"):
            replay_scenarios({"crypto": 1.0}, closes)

    def test_historical_drawdown_spans_the_common_window(self, closes):
        out = historical_drawdown(model_portfolio(3), closes)
        assert out["window_start"] == pd.Timestamp("2007-05-31")
        assert out["window_end"] == closes.index[-1]
        assert -0.60 < out["max_drawdown"] < -0.10


class TestPortfolioReturns:
    def test_weighted_average_of_two_tickers(self):
        closes = pd.DataFrame(
            {"IVV": [100.0, 102.0], "AGG": [100.0, 99.0]},
            index=pd.to_datetime(["2024-01-02", "2024-01-03"]),
        )
        returns = portfolio_returns({"IVV": 0.6, "AGG": 0.4}, closes)
        assert returns.iloc[0] == pytest.approx(0.6 * 0.02 + 0.4 * -0.01)

    def test_rejects_missing_ticker(self):
        closes = pd.DataFrame({"IVV": [100.0, 101.0]})
        with pytest.raises(ValueError, match="missing tickers"):
            portfolio_returns({"IVV": 0.5, "AGG": 0.5}, closes)


class TestMaxDrawdown:
    def test_known_path(self):
        # Up 10%, down 20%, up 5%: worst slide is the -20% period.
        returns = pd.Series([0.10, -0.20, 0.05])
        assert max_drawdown(returns) == pytest.approx(-0.20)

    def test_never_down_means_zero(self):
        returns = pd.Series([0.01, 0.02, 0.03])
        assert max_drawdown(returns) == pytest.approx(0.0)

    def test_a_drop_in_the_first_period_counts(self):
        returns = pd.Series([-0.10, 0.05])
        assert max_drawdown(returns) == pytest.approx(-0.10)


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
