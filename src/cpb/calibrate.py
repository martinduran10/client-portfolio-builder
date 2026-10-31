"""Numbers in the allocation tables that come from the proxy history.

Volatility of a model mix is the standard deviation of its monthly
returns over the longest window every proxy ETF shares, times the square
root of twelve.  ``python -m cpb.calibrate`` prints the table that
``allocation.MODEL_VOLATILITY`` must match; a test enforces the match so
the constants cannot drift from the data.
"""

from __future__ import annotations

import math

import pandas as pd

from .allocation import MODEL_PORTFOLIOS
from .implementation import ticker_weights
from .proxies import MONTHS_PER_YEAR, PROXY_MAP, common_closes, common_window, load_proxies
from .stress import portfolio_returns


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


if __name__ == "__main__":  # pragma: no cover
    closes = load_proxies()
    start, end = common_window(closes)
    print(f"# monthly returns {start + pd.offsets.MonthEnd(1):%Y-%m} to {end:%Y-%m}, annualized by sqrt(12)")
    print("MODEL_VOLATILITY = {")
    for level, vol in model_volatilities(closes).items():
        print(f"    {level}: {vol},")
    print("}")
