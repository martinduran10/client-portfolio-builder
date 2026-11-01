"""Numbers in the profile and allocation tables that come from the proxy
history.

Volatility of a model mix is the standard deviation of its monthly
returns over the longest window every proxy ETF shares, times the square
root of twelve.  A level's loss-tolerance band is that level's worst
calendar-year loss on the 2008/2020/2022 replays, rounded to the nearest
whole percent.  ``python -m cpb.calibrate`` prints both tables;
``allocation.MODEL_VOLATILITY`` and ``profile.LOSS_TOLERANCE_BANDS``
must match them, and tests enforce the match so the constants cannot
drift from the data.
"""

from __future__ import annotations

import math

import pandas as pd

from .allocation import MODEL_PORTFOLIOS
from .implementation import ticker_weights
from .proxies import (
    MONTHS_PER_YEAR,
    PROXY_MAP,
    common_closes,
    common_window,
    load_daily_proxies,
    load_proxies,
)
from .stress import portfolio_returns, replay_scenarios

CAPPED_LEVELS = (1, 2, 3, 4)  # level 5 has no loss cap


def historical_volatility(
    weights: dict[str, float],
    closes: pd.DataFrame,
    proxy_map: dict[str, str] | None = None,
) -> float:
    """Annualized volatility of the mix: the standard deviation of its
    monthly returns over the longest common window, times sqrt(12)."""
    closes = common_closes(closes)
    returns = portfolio_returns(ticker_weights(weights, proxy_map or PROXY_MAP), closes)
    return float(returns.std(ddof=1) * math.sqrt(MONTHS_PER_YEAR))


def model_volatilities(closes: pd.DataFrame | None = None, digits: int = 4) -> dict[int, float]:
    """The volatility of every model portfolio, rounded for the table."""
    closes = load_proxies() if closes is None else closes
    return {
        level: round(historical_volatility(weights, closes), digits)
        for level, weights in MODEL_PORTFOLIOS.items()
    }


def loss_tolerance_bands(
    daily: pd.DataFrame | None = None,
    monthly: pd.DataFrame | None = None,
) -> tuple[tuple[float, int], ...]:
    """Each capped level's band: its worst calendar-year loss on the
    replays, as a positive fraction rounded to the nearest whole percent."""
    daily = load_daily_proxies() if daily is None else daily
    monthly = load_proxies() if monthly is None else monthly
    bands = []
    for level in CAPPED_LEVELS:
        table = replay_scenarios(MODEL_PORTFOLIOS[level], daily, monthly)
        worst = float(table["calendar_year_return"].min())
        bands.append((round(-worst, 2), level))
    return tuple(bands)


if __name__ == "__main__":  # pragma: no cover
    closes = load_proxies()
    start, end = common_window(closes)
    print(f"# monthly returns {start + pd.offsets.MonthEnd(1):%Y-%m} to {end:%Y-%m}, annualized by sqrt(12)")
    print("MODEL_VOLATILITY = {")
    for level, vol in model_volatilities(closes).items():
        print(f"    {level}: {vol},")
    print("}")
    print("# worst calendar-year loss per level on the 2008/2020/2022 replays, whole percent")
    print(f"LOSS_TOLERANCE_BANDS = {loss_tolerance_bands(monthly=closes)}")
