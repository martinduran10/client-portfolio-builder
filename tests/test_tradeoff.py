"""The trade-off table puts the recommended level beside the next one up."""

import pytest

from cpb.allocation import expected_return, expected_volatility, model_portfolio
from cpb.stress import goal_miss_probability
from cpb.tradeoff import level_summary, tradeoff_table


@pytest.fixture(scope="module")
def table():
    return tradeoff_table(2, 5_000_000, 10_000_000, 15)


def test_two_rows_recommended_then_next_level_up(table):
    assert list(table.index) == [2, 3]
    assert list(table["name"]) == ["Moderately Conservative", "Balanced"]


def test_next_level_up_earns_more_and_loses_more(table):
    low, high = table.loc[2], table.loc[3]
    assert high["expected_return"] > low["expected_return"]
    assert high["volatility"] > low["volatility"]
    assert high["worst_year_return"] < low["worst_year_return"]
    assert high["crisis_2008_slide"] < low["crisis_2008_slide"]


def test_odds_match_the_monte_carlo_for_the_same_inputs(table):
    weights = model_portfolio(2)
    direct = goal_miss_probability(
        5_000_000, 10_000_000, 15, expected_return(weights), expected_volatility(2)
    )
    assert table.loc[2, "miss_probability"] == direct


def test_level_5_has_no_next_level(table):
    top = tradeoff_table(5, 5_000_000, 10_000_000, 15)
    assert list(top.index) == [5]


def test_summary_names_the_worst_year(table):
    row = level_summary(3, 5_000_000, 10_000_000, 15)
    assert row["worst_year"] == 2008
    assert row["worst_year_return"] == pytest.approx(-0.2134, abs=0.001)


def test_rejects_unknown_level():
    with pytest.raises(ValueError, match="risk level"):
        tradeoff_table(6, 5_000_000, 10_000_000, 15)
