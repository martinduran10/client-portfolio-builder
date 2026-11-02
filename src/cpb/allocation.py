"""Five model portfolios and plain building-block return estimates.

Each risk level 1-5 owns a fixed asset-class mix; the 10-year return
estimate is just the weighted average of per-asset estimates, nudged by
a simple valuation rule: if an asset trades above its own 10-year
average valuation, we shave a tenth of that premium off the return each
year (mean reversion spread over a decade), capped at ±2% a year.
"""

from __future__ import annotations

ASSET_CLASSES = (
    "us_equity",
    "intl_equity",
    "em_equity",
    "core_bonds",
    "short_bonds",
    "cash",
)

# Weights are fractions and sum to 1 at every level.
# Equity share steps 15% → 35% → 55% → 75% → 95%.
MODEL_PORTFOLIOS = {
    1: {"us_equity": 0.10, "intl_equity": 0.05, "em_equity": 0.00,
        "core_bonds": 0.45, "short_bonds": 0.30, "cash": 0.10},
    2: {"us_equity": 0.20, "intl_equity": 0.10, "em_equity": 0.05,
        "core_bonds": 0.45, "short_bonds": 0.15, "cash": 0.05},
    3: {"us_equity": 0.30, "intl_equity": 0.15, "em_equity": 0.10,
        "core_bonds": 0.35, "short_bonds": 0.07, "cash": 0.03},
    4: {"us_equity": 0.42, "intl_equity": 0.20, "em_equity": 0.13,
        "core_bonds": 0.20, "short_bonds": 0.03, "cash": 0.02},
    5: {"us_equity": 0.55, "intl_equity": 0.25, "em_equity": 0.15,
        "core_bonds": 0.05, "short_bonds": 0.00, "cash": 0.00},
}

MODEL_NAMES = {
    1: "Conservative",
    2: "Moderately Conservative",
    3: "Balanced",
    4: "Growth",
    5: "Aggressive",
}

# Long-run 10-year annual return estimates per asset class, before any
# valuation adjustment.  Simple building blocks: income plus growth.
TEN_YEAR_RETURNS = {
    "us_equity": 0.065,
    "intl_equity": 0.070,
    "em_equity": 0.075,
    "core_bonds": 0.040,
    "short_bonds": 0.035,
    "cash": 0.030,
}

# Annual volatility of each model mix, computed from the history of that
# mix: standard deviation of monthly returns on the proxy ETFs in
# data/proxies.csv over the longest window they all share (2007-06 to
# 2026-10), times sqrt(12).  Regenerate with ``python -m cpb.calibrate``;
# tests/test_allocation.py fails if these drift from the data.
MODEL_VOLATILITY = {1: 0.0375, 2: 0.0654, 3: 0.0944, 4: 0.123, 5: 0.152}

# The valuation nudge never moves a return estimate more than this per year.
MAX_VALUATION_ADJUSTMENT = 0.02


def model_portfolio(level: int) -> dict[str, float]:
    """The fixed asset-class mix for a risk level 1-5."""
    if level not in MODEL_PORTFOLIOS:
        raise ValueError(f"risk level must be 1-5, got {level}")
    return dict(MODEL_PORTFOLIOS[level])


def valuation_adjustment(premium: float) -> float:
    """Annual return nudge for an asset trading rich or cheap.

    If the asset is ``premium`` above its own 10-year average valuation
    (0.25 = 25% rich), shave a tenth of that off the return each year,
    capped at ±2% a year.  Cheap assets get the same nudge upward.
    """
    tenth = premium / 10.0
    return -min(max(tenth, -MAX_VALUATION_ADJUSTMENT), MAX_VALUATION_ADJUSTMENT)


def expected_return(
    weights: dict[str, float],
    valuation_premiums: dict[str, float] | None = None,
) -> float:
    """10-year annual return estimate: the weighted average of per-asset
    estimates after the valuation nudge."""
    premiums = valuation_premiums or {}
    unknown = set(weights) - set(TEN_YEAR_RETURNS)
    if unknown:
        raise ValueError(f"no return estimate for asset classes: {sorted(unknown)}")
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("weights must sum to 1")
    return sum(
        w * (TEN_YEAR_RETURNS[asset] + valuation_adjustment(premiums.get(asset, 0.0)))
        for asset, w in weights.items()
    )


def expected_volatility(level: int) -> float:
    """The long-run annual volatility assumed for a risk level's mix."""
    if level not in MODEL_VOLATILITY:
        raise ValueError(f"risk level must be 1-5, got {level}")
    return MODEL_VOLATILITY[level]
