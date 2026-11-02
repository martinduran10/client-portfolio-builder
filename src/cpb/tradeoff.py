"""Compare the recommended level with the next one up: what more return
and more confidence of reaching the goal cost in a bad year.

One rule: reaching the goal with higher confidence requires accepting a
larger loss in a bad year, and the table shows both sides for the two
levels side by side.
"""

from __future__ import annotations

import pandas as pd

from .allocation import MODEL_NAMES, expected_return, expected_volatility, model_portfolio
from .stress import DEFAULT_N_PATHS, goal_miss_probability, replay_scenarios

CRISIS = "2008 global financial crisis"


def level_summary(
    level: int,
    initial_usd: float,
    target_usd: float,
    horizon_years: int,
    valuation_premiums: dict[str, float] | None = None,
    daily: pd.DataFrame | None = None,
    monthly: pd.DataFrame | None = None,
    n_paths: int = DEFAULT_N_PATHS,
    seed: int = 42,
) -> dict[str, object]:
    """The four numbers a banker compares across levels: worst replayed
    calendar year, the 2008 peak-to-trough slide, the expected return,
    and the odds of missing the goal."""
    weights = model_portfolio(level)
    table = replay_scenarios(weights, daily, monthly)
    worst = table["calendar_year_return"].idxmin()
    mu = expected_return(weights, valuation_premiums)
    sigma = expected_volatility(level)
    return {
        "level": level,
        "name": MODEL_NAMES[level],
        "worst_year_return": float(table.loc[worst, "calendar_year_return"]),
        "worst_year": int(table.loc[worst, "calendar_year"]),
        "crisis_2008_slide": float(table.loc[CRISIS, "peak_to_trough"]),
        "expected_return": mu,
        "volatility": sigma,
        "miss_probability": goal_miss_probability(
            initial_usd, target_usd, horizon_years, mu, sigma, n_paths=n_paths, seed=seed
        ),
    }


def tradeoff_table(
    level: int,
    initial_usd: float,
    target_usd: float,
    horizon_years: int,
    **kwargs,
) -> pd.DataFrame:
    """Two rows, the recommended level and the next level up (one row at
    level 5), indexed by level."""
    if level not in MODEL_NAMES:
        raise ValueError(f"risk level must be 1-5, got {level}")
    levels = [level] + ([level + 1] if level < 5 else [])
    rows = [level_summary(lvl, initial_usd, target_usd, horizon_years, **kwargs) for lvl in levels]
    return pd.DataFrame(rows).set_index("level")
