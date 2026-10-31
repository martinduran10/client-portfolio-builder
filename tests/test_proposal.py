"""The proposal page carries every number the banker needs, on one page."""

from datetime import date

import pytest

from cpb.allocation import expected_return, model_portfolio
from cpb.implementation import to_holdings
from cpb.profile import ClientProfile
from cpb.proposal import render_proposal, write_proposal
from cpb.stress import replay_scenarios


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
    weights = model_portfolio(3)
    return dict(
        profile=profile,
        level=3,
        holdings=to_holdings(weights, profile.total_assets_usd),
        expected_return=expected_return(weights),
        scenarios=replay_scenarios(weights),
        target_usd=10_000_000,
        miss_probability=0.47,
        fx={"offshore_usd": 3_000_000, "onshore_usd": 2_000_000, "depreciation": 0.20},
        as_of=date(2026, 10, 31),
    )


def test_contains_the_key_facts(pieces):
    html = render_proposal(**pieces)
    assert "Bogotá family" in html
    assert "Level 3" in html
    assert "Balanced" in html
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
