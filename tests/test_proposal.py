"""The proposal page carries every number the banker needs, on one page."""

from datetime import date

import pytest

from cpb.allocation import expected_return, model_portfolio
from cpb.implementation import to_holdings
from cpb.profile import ClientProfile
from cpb.proposal import render_proposal, write_proposal
from cpb.stress import historical_drawdown, replay_scenarios
from cpb.tradeoff import tradeoff_table


@pytest.fixture
def pieces():
    profile = ClientProfile(
        name="Bogotá family",
        total_assets_usd=5_000_000,
        horizon_years=15,
        goal="grow",
        max_annual_loss=0.15,
        offshore_share=0.60,
        local_currency="COP",
    )
    weights = model_portfolio(2)  # a 15% tolerance holds level 2, not 3
    return dict(
        profile=profile,
        level=2,
        holdings=to_holdings(weights, profile.total_assets_usd),
        expected_return=expected_return(weights),
        scenarios=replay_scenarios(weights),
        drawdown=historical_drawdown(weights),
        target_usd=10_000_000,
        miss_probability=0.47,
        n_paths=10_000,
        tradeoff=tradeoff_table(2, profile.total_assets_usd, 10_000_000, 15),
        fx={"offshore_usd": 3_000_000, "onshore_usd": 2_000_000, "depreciation": 0.20},
        as_of=date(2026, 10, 31),
    )


def test_contains_the_key_facts(pieces):
    html = render_proposal(**pieces)
    assert "Bogotá family" in html
    assert "Level 2" in html
    assert "Conservative Income" in html
    assert "IVV" in html
    assert "$5,000,000" in html
    assert "$10,000,000" in html
    assert "47%" in html
    assert "2026-10-31" in html


def test_fx_section_only_when_given(pieces):
    with_fx = render_proposal(**pieces)
    assert "COP" in with_fx
    pieces["fx"] = None
    without_fx = render_proposal(**pieces)
    assert "Currency" not in without_fx


def test_scenario_rows_show_dollar_impact(pieces):
    html = render_proposal(**pieces)
    assert "2022 rate shock" in html
    assert "Jan 2022–Dec 2022" in html
    # The dollar column is the peak-to-trough slide times the portfolio.
    slide = pieces["scenarios"].loc["2022 rate shock", "peak_to_trough"]
    dollars = slide * pieces["profile"].total_assets_usd
    assert f"${dollars:,.0f}" in html


def test_write_proposal_creates_parents(tmp_path, pieces):
    html = render_proposal(**pieces)
    out = write_proposal(html, tmp_path / "out" / "proposal.html")
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("<!DOCTYPE html>")


def test_path_count_is_the_one_passed_in(pieces):
    assert "10,000 simulated futures" in render_proposal(**pieces)
    pieces["n_paths"] = 2_500
    assert "2,500 simulated futures" in render_proposal(**pieces)


def test_drawdown_line_shows_the_worst_slide(pieces):
    html = render_proposal(**pieces)
    dd = pieces["drawdown"]["max_drawdown"]
    assert f"{dd * 100:.1f}%" in html
    assert "May 2007 to" in html


def test_currency_is_a_stress_not_a_drift(pieces):
    html = render_proposal(**pieces)
    assert "If the COP weakened 20%" in html
    assert "No currency drift is built into" in html
    assert "expected to slide" not in html


def test_risk_section_states_the_worst_year_and_the_2008_slide(pieces):
    html = render_proposal(**pieces)
    assert "this mix lost 12% in its worst year, within the 15%" in html
    assert "the next level up lost 21%" in html
    slide = -pieces["scenarios"].loc["2008 global financial crisis", "peak_to_trough"]
    assert f"In a crisis like 2008, this portfolio fell {slide * 100:.1f}% from peak to trough." in html


def test_risk_section_warns_when_no_mix_fits(pieces):
    from dataclasses import replace

    pieces["profile"] = replace(pieces["profile"], max_annual_loss=0.05)
    pieces["level"] = 1
    pieces["holdings"] = to_holdings(model_portfolio(1), 5_000_000)
    html = render_proposal(**pieces)
    assert "No model portfolio fits the stated 5% bad-year tolerance" in html
    assert "the most conservative mix lost 9%" in html


def test_tradeoff_section_compares_the_next_level_up(pieces):
    html = render_proposal(**pieces)
    assert "<h2>Trade-off</h2>" in html
    assert "Level 2 — Conservative Income <span class='meta'>(recommended)</span>" in html
    assert "Level 3 — Balanced <span class='meta'>(next level up)</span>" in html
    assert "Reaching the goal with higher confidence requires accepting a larger loss in a bad year." in html
    next_up = pieces["tradeoff"].loc[3]
    assert f"{next_up.miss_probability * 100:.0f}%" in html
