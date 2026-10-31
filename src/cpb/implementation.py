"""Turn an asset-class mix into ETF tickers and dollar amounts.

One liquid ETF per asset class; each holding's dollar amount is simply
its weight times the portfolio value.
"""

from __future__ import annotations

import pandas as pd

DEFAULT_ETF_MAP = {
    "us_equity": "IVV",
    "intl_equity": "IEFA",
    "em_equity": "IEMG",
    "core_bonds": "AGG",
    "short_bonds": "SHY",
    "cash": "BIL",
}

ETF_NAMES = {
    "IVV": "iShares Core S&P 500",
    "IEFA": "iShares Core MSCI EAFE",
    "IEMG": "iShares Core MSCI Emerging Markets",
    "AGG": "iShares Core U.S. Aggregate Bond",
    "SHY": "iShares 1-3 Year Treasury Bond",
    "BIL": "SPDR 1-3 Month T-Bill",
}


def to_holdings(
    weights: dict[str, float],
    total_usd: float,
    etf_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """One row per asset class: ticker, weight, dollars (weight × total).

    Zero-weight classes are dropped; rows are sorted largest first.
    """
    etf_map = etf_map or DEFAULT_ETF_MAP
    missing = set(weights) - set(etf_map)
    if missing:
        raise ValueError(f"no ETF mapped for asset classes: {sorted(missing)}")
    if total_usd <= 0:
        raise ValueError("total_usd must be positive")
    rows = [
        {
            "asset_class": asset,
            "ticker": etf_map[asset],
            "weight": w,
            "amount_usd": round(w * total_usd, 2),
        }
        for asset, w in weights.items()
        if w > 0
    ]
    holdings = pd.DataFrame(rows).sort_values("weight", ascending=False)
    return holdings.reset_index(drop=True)


def ticker_weights(
    weights: dict[str, float],
    etf_map: dict[str, str] | None = None,
) -> dict[str, float]:
    """Collapse asset-class weights onto their ETF tickers."""
    etf_map = etf_map or DEFAULT_ETF_MAP
    out: dict[str, float] = {}
    for asset, w in weights.items():
        if w <= 0:
            continue
        ticker = etf_map[asset]
        out[ticker] = out.get(ticker, 0.0) + w
    return out
