"""Stress tests a banker can narrate: replay three bad years, measure the
worst historical slide, and count the simulated futures that miss the goal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# What each asset class actually returned in three distinct bad episodes.
# 2008: credit crisis, bonds cushioned.  2020: fast crash, little cushion
# over the five-week slide.  2022: rate shock, bonds fell with stocks.
SCENARIOS = {
    "2008 global financial crisis": {
        "us_equity": -0.37, "intl_equity": -0.43, "em_equity": -0.53,
        "core_bonds": 0.05, "short_bonds": 0.07, "cash": 0.02,
    },
    "2020 covid crash": {
        "us_equity": -0.34, "intl_equity": -0.33, "em_equity": -0.32,
        "core_bonds": -0.01, "short_bonds": 0.01, "cash": 0.00,
    },
    "2022 rate shock": {
        "us_equity": -0.18, "intl_equity": -0.14, "em_equity": -0.20,
        "core_bonds": -0.13, "short_bonds": -0.04, "cash": 0.015,
    },
}


def scenario_return(weights: dict[str, float], scenario: str) -> float:
    """If this episode happened again, the mix would move by the weighted
    average of what each asset class did back then."""
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario {scenario!r}; pick from {sorted(SCENARIOS)}")
    shocks = SCENARIOS[scenario]
    unknown = set(weights) - set(shocks)
    if unknown:
        raise ValueError(f"no scenario return for asset classes: {sorted(unknown)}")
    return sum(w * shocks[asset] for asset, w in weights.items())


def run_scenarios(weights: dict[str, float]) -> dict[str, float]:
    """Portfolio return under every stored scenario."""
    return {name: scenario_return(weights, name) for name in SCENARIOS}


def portfolio_daily_returns(
    ticker_weights: dict[str, float],
    closes: pd.DataFrame,
) -> pd.Series:
    """Daily return of the mix: each day's weighted average of the
    holdings' returns (weights held constant, i.e. rebalanced daily)."""
    missing = set(ticker_weights) - set(closes.columns)
    if missing:
        raise ValueError(f"closes are missing tickers: {sorted(missing)}")
    returns = closes[list(ticker_weights)].pct_change().dropna(how="any")
    weights = pd.Series(ticker_weights)
    return (returns * weights).sum(axis=1)


def max_drawdown(returns: pd.Series) -> float:
    """Worst peak-to-trough slide of the growth-of-a-dollar curve,
    as a negative fraction."""
    curve = (1.0 + returns).cumprod()
    drawdown = curve / curve.cummax() - 1.0
    return float(drawdown.min())


def goal_miss_probability(
    initial_usd: float,
    target_usd: float,
    horizon_years: int,
    expected_return: float,
    volatility: float,
    n_paths: int = 10_000,
    seed: int = 42,
) -> float:
    """Fraction of simulated futures that end below the goal.

    Each future is ``horizon_years`` annual returns drawn from a normal
    distribution with the portfolio's expected return and volatility,
    compounded from the starting value.  A year can never lose more
    than everything.
    """
    if initial_usd <= 0 or target_usd <= 0:
        raise ValueError("initial_usd and target_usd must be positive")
    if horizon_years <= 0:
        raise ValueError("horizon_years must be positive")
    rng = np.random.default_rng(seed)
    annual = rng.normal(expected_return, volatility, size=(n_paths, int(horizon_years)))
    growth = np.maximum(1.0 + annual, 0.0)
    terminal = initial_usd * growth.prod(axis=1)
    return float((terminal < target_usd).mean())
