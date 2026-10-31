"""Loader for Bloomberg daily closes kept outside the repo.

The file is a wide CSV: first column dates, one column per ticker,
values are daily closing prices.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_closes(csv_path: str | Path) -> pd.DataFrame:
    """Read a wide CSV of daily closes into a date-indexed frame."""
    closes = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    closes.index.name = "date"
    return closes.sort_index()


def daily_returns(closes: pd.DataFrame) -> pd.DataFrame:
    """Day-over-day percentage change of each ticker's close."""
    return closes.pct_change().dropna(how="all")
