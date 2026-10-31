"""Stress tests a banker can narrate: replay three bad episodes on the
proxy ETF history, measure the worst month-end slide, and count the
simulated futures that miss the goal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .implementation import ticker_weights
from .proxies import PROXY_MAP, common_closes, load_proxies

# Each episode reports two numbers: the full calendar-year return, and the
# peak-to-trough slide inside a window of month-ends (inclusive).
# Simulated futures in the goal-miss count; the proposal prints the number
# actually used, so pass the same value to both.
DEFAULT_N_PATHS = 10_000

SCENARIO_WINDOWS = {
    "2008 global financial crisis": {"calendar_year": 2008, "window": ("2007-10", "2009-02")},
    "2020 covid crash": {"calendar_year": 2020, "window": ("2020-02", "2020-03")},
    "2022 rate shock": {"calendar_year": 2022, "window": ("2022-01", "2022-12")},
}


def portfolio_returns(ticker_weights: dict[str, float], closes: pd.DataFrame) -> pd.Series:
    """Period return of the mix: each period's weighted average of the
    holdings' returns (weights held constant, i.e. rebalanced every period)."""
    missing = set(ticker_weights) - set(closes.columns)
    if missing:
        raise ValueError(f"closes are missing tickers: {sorted(missing)}")
    returns = closes[list(ticker_weights)].pct_change().dropna(how="any")
    weights = pd.Series(ticker_weights)
    return (returns * weights).sum(axis=1)


def max_drawdown(returns: pd.Series) -> float:
    """Worst peak-to-trough slide of the growth-of-a-dollar curve, counting
    the dollar you started with, as a negative fraction."""
    curve = np.concatenate([[1.0], np.cumprod(1.0 + np.asarray(returns, dtype=float))])
    peak = np.maximum.accumulate(curve)
    return float((curve / peak - 1.0).min())


def _month_end(label: str) -> pd.Timestamp:
    return pd.Timestamp(label) + pd.offsets.MonthEnd(0)


def window_returns(returns: pd.Series, start: str, end: str) -> pd.Series:
    """The monthly returns from ``start`` to ``end`` inclusive, given as
    ``"YYYY-MM"``; the first month's return is measured from the month-end
    before the window."""
    window = returns.loc[_month_end(start):_month_end(end)]
    if window.empty:
        raise ValueError(f"no returns between {start} and {end}")
    return window


def calendar_year_return(returns: pd.Series, year: int) -> float:
    """Compounded return over the twelve months of ``year``."""
    months = returns.loc[str(year)]
    if len(months) != 12:
        raise ValueError(f"{year} has {len(months)} months of returns, need 12")
    return float((1.0 + months).prod() - 1.0)


def peak_to_trough(returns: pd.Series, start: str, end: str) -> float:
    """Worst slide inside the window, from the month-end before it starts."""
    return max_drawdown(window_returns(returns, start, end))


def _proxy_weights(weights: dict[str, float], proxy_map: dict[str, str] | None) -> dict[str, float]:
    proxy_map = proxy_map or PROXY_MAP
    unknown = set(weights) - set(proxy_map)
    if unknown:
        raise ValueError(f"no proxy for asset classes: {sorted(unknown)}")
    return ticker_weights(weights, proxy_map)


def replay_scenarios(
    weights: dict[str, float],
    closes: pd.DataFrame | None = None,
    proxy_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """If each episode happened again, what the mix would do: one row per
    scenario with the calendar-year return and the peak-to-trough slide,
    replayed on the proxy ETFs' month-end history."""
    closes = load_proxies() if closes is None else closes
    returns = portfolio_returns(_proxy_weights(weights, proxy_map), closes)
    rows = []
    for name, spec in SCENARIO_WINDOWS.items():
        start, end = spec["window"]
        rows.append({
            "scenario": name,
            "calendar_year": spec["calendar_year"],
            "calendar_year_return": calendar_year_return(returns, spec["calendar_year"]),
            "window_start": start,
            "window_end": end,
            "peak_to_trough": peak_to_trough(returns, start, end),
        })
    return pd.DataFrame(rows).set_index("scenario")


def asset_class_scenarios(
    closes: pd.DataFrame | None = None,
    proxy_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """The same two numbers for each asset class on its own, so the banker
    can say what every building block did in each episode."""
    closes = load_proxies() if closes is None else closes
    proxy_map = proxy_map or PROXY_MAP
    rows = []
    for asset, ticker in proxy_map.items():
        returns = closes[ticker].pct_change().dropna()
        for name, spec in SCENARIO_WINDOWS.items():
            start, end = spec["window"]
            rows.append({
                "scenario": name,
                "asset_class": asset,
                "ticker": ticker,
                "calendar_year_return": calendar_year_return(returns, spec["calendar_year"]),
                "peak_to_trough": peak_to_trough(returns, start, end),
            })
    return pd.DataFrame(rows).set_index(["scenario", "asset_class"])


def historical_drawdown(
    weights: dict[str, float],
    closes: pd.DataFrame | None = None,
    proxy_map: dict[str, str] | None = None,
) -> dict[str, object]:
    """Worst month-end slide of the mix over the longest window every proxy
    shares, with the window's first and last month-end."""
    closes = common_closes(load_proxies() if closes is None else closes)
    returns = portfolio_returns(_proxy_weights(weights, proxy_map), closes)
    return {
        "max_drawdown": max_drawdown(returns),
        "window_start": closes.index[0],
        "window_end": closes.index[-1],
    }


def goal_miss_probability(
    initial_usd: float,
    target_usd: float,
    horizon_years: int,
    expected_return: float,
    volatility: float,
    n_paths: int = DEFAULT_N_PATHS,
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
