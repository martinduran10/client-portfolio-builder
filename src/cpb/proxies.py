"""Long-history monthly closes for the ETF proxies behind each asset class.

Yahoo Finance adjusted closes (dividends reinvested) are downloaded once
with ``yfinance``, resampled to month-end, and cached in
``data/proxies.csv``.  Tests, CI and the worked example read the cache,
so nothing in the package needs the network after a refresh.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROXIES_CSV = Path(__file__).resolve().parents[2] / "data" / "proxies.csv"

# Ticker → what it stands for.  HYG and GLD are kept in the history for
# future asset classes; no model portfolio holds them yet.
PROXY_TICKERS = {
    "SPY": "US equity (S&P 500)",
    "EFA": "developed ex-US equity (MSCI EAFE)",
    "EEM": "emerging-market equity (MSCI EM)",
    "AGG": "US investment-grade bonds (Bloomberg US Aggregate)",
    "SHY": "1-3 year Treasuries",
    "BIL": "1-3 month T-bills (cash)",
    "HYG": "US high-yield bonds (not yet in a model portfolio)",
    "GLD": "gold (not yet in a model portfolio)",
}

# Asset class → the proxy that stands in for it in replays and volatility.
PROXY_MAP = {
    "us_equity": "SPY",
    "intl_equity": "EFA",
    "em_equity": "EEM",
    "core_bonds": "AGG",
    "short_bonds": "SHY",
    "cash": "BIL",
}

MONTHS_PER_YEAR = 12


def download_monthly_closes(
    tickers: list[str] | None = None,
    start: str = "1990-01-01",
) -> pd.DataFrame:
    """Fetch daily adjusted closes from Yahoo Finance and keep each
    month's last close.  A month still in progress is dropped.

    Needs the optional ``yfinance`` dependency and network access.
    """
    import yfinance as yf  # optional; only the refresh needs it

    tickers = list(tickers or PROXY_TICKERS)
    daily = yf.download(
        tickers, start=start, interval="1d", auto_adjust=True, progress=False
    )["Close"]
    daily = daily[tickers].sort_index()
    daily.index = pd.to_datetime(daily.index).tz_localize(None)
    monthly = daily.resample("ME").last()
    last_day = daily.index[-1]
    if last_day < last_day + pd.offsets.BMonthEnd(0):
        monthly = monthly.iloc[:-1]
    monthly.index.name = "date"
    return monthly.round(4)


def refresh_cache(path: str | Path = PROXIES_CSV, **kwargs) -> Path:
    """Download the proxy history and write it to the CSV cache."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    download_monthly_closes(**kwargs).to_csv(path)
    return path


def load_proxies(path: str | Path = PROXIES_CSV) -> pd.DataFrame:
    """Read the cached month-end closes: date index, one column per ticker."""
    closes = pd.read_csv(path, index_col=0, parse_dates=True)
    closes.index.name = "date"
    return closes.sort_index()


def monthly_returns(closes: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month change of each ticker's close."""
    return closes.pct_change().iloc[1:]


def common_window(closes: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """First and last month-end where every ticker has a close: the
    longest window the whole proxy set shares."""
    full = closes.dropna(how="any")
    if full.empty:
        raise ValueError("no month where every ticker has a close")
    return full.index[0], full.index[-1]


def common_closes(closes: pd.DataFrame) -> pd.DataFrame:
    """The closes restricted to the longest common window."""
    start, end = common_window(closes)
    return closes.loc[start:end]


if __name__ == "__main__":  # pragma: no cover
    out = refresh_cache()
    closes = load_proxies(out)
    first, last = common_window(closes)
    print(f"wrote {out}: {len(closes)} month-ends, {closes.index[0]:%Y-%m} to {closes.index[-1]:%Y-%m}")
    print(f"longest common window: {first:%Y-%m} to {last:%Y-%m}")
    print(closes.notna().idxmax().rename("first close").to_string())
