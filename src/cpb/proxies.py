"""Long-history closes for the ETF proxies behind each asset class.

Yahoo Finance adjusted closes (dividends reinvested) are downloaded once
with ``yfinance`` and cached twice: every trading day in
``data/proxies_daily.csv`` for drawdowns and scenario replays, and each
month's last close in ``data/proxies.csv`` for volatility and the Monte
Carlo.  Tests, CI and the worked example read the caches, so nothing in
the package needs the network after a refresh.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_DATA = Path(__file__).resolve().parents[2] / "data"
PROXIES_CSV = _DATA / "proxies.csv"
PROXIES_DAILY_CSV = _DATA / "proxies_daily.csv"

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


def download_daily_closes(
    tickers: list[str] | None = None,
    start: str = "1990-01-01",
) -> pd.DataFrame:
    """Fetch daily adjusted closes from Yahoo Finance, one column per
    ticker, rounded to four decimals.

    Needs the optional ``yfinance`` dependency and network access.
    """
    import yfinance as yf  # optional; only the refresh needs it

    tickers = list(tickers or PROXY_TICKERS)
    daily = yf.download(
        tickers, start=start, interval="1d", auto_adjust=True, progress=False
    )["Close"]
    daily = daily[tickers].sort_index()
    daily.index = pd.to_datetime(daily.index).tz_localize(None)
    daily.index.name = "date"
    return daily.round(4)


def to_month_ends(daily: pd.DataFrame) -> pd.DataFrame:
    """Each month's last close, labelled by calendar month-end.  A month
    still in progress on the last row is dropped."""
    monthly = daily.resample("ME").last()
    last_day = daily.index[-1]
    if last_day < last_day + pd.offsets.BMonthEnd(0):
        monthly = monthly.iloc[:-1]
    monthly.index.name = "date"
    return monthly


def download_monthly_closes(
    tickers: list[str] | None = None,
    start: str = "1990-01-01",
) -> pd.DataFrame:
    """Month-end closes straight from a fresh daily download."""
    return to_month_ends(download_daily_closes(tickers, start))


def refresh_cache(
    daily_path: str | Path = PROXIES_DAILY_CSV,
    monthly_path: str | Path = PROXIES_CSV,
    **kwargs,
) -> tuple[Path, Path]:
    """Download once and write both caches, so the month-ends are exactly
    the last rows of each month in the daily file."""
    daily_path, monthly_path = Path(daily_path), Path(monthly_path)
    daily_path.parent.mkdir(parents=True, exist_ok=True)
    daily = download_daily_closes(**kwargs)
    daily.to_csv(daily_path)
    to_month_ends(daily).to_csv(monthly_path)
    return daily_path, monthly_path


def _load(path: str | Path) -> pd.DataFrame:
    closes = pd.read_csv(path, index_col=0, parse_dates=True)
    closes.index.name = "date"
    return closes.sort_index()


def load_proxies(path: str | Path = PROXIES_CSV) -> pd.DataFrame:
    """Read the cached month-end closes: date index, one column per ticker."""
    return _load(path)


def load_daily_proxies(path: str | Path = PROXIES_DAILY_CSV) -> pd.DataFrame:
    """Read the cached daily closes: trading-day index, one column per ticker."""
    return _load(path)


def monthly_returns(closes: pd.DataFrame) -> pd.DataFrame:
    """Month-over-month change of each ticker's close."""
    return closes.pct_change().iloc[1:]


def common_window(closes: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """First and last date where every ticker has a close: the longest
    window the whole proxy set shares."""
    full = closes.dropna(how="any")
    if full.empty:
        raise ValueError("no date where every ticker has a close")
    return full.index[0], full.index[-1]


def common_closes(closes: pd.DataFrame) -> pd.DataFrame:
    """The closes restricted to the longest common window."""
    start, end = common_window(closes)
    return closes.loc[start:end]


if __name__ == "__main__":  # pragma: no cover
    daily_out, monthly_out = refresh_cache()
    daily, monthly = load_daily_proxies(daily_out), load_proxies(monthly_out)
    print(f"wrote {daily_out}: {len(daily)} trading days, {daily.index[0]:%Y-%m-%d} to {daily.index[-1]:%Y-%m-%d}")
    print(f"wrote {monthly_out}: {len(monthly)} month-ends, {monthly.index[0]:%Y-%m} to {monthly.index[-1]:%Y-%m}")
    first, last = common_window(daily)
    print(f"longest common window (daily): {first:%Y-%m-%d} to {last:%Y-%m-%d}")
    print(daily.notna().idxmax().rename("first close").to_string())
