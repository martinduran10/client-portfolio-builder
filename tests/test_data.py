"""The loader reads a wide CSV of closes into a sorted, date-indexed frame."""

import pandas as pd
import pytest

from cpb.data import daily_returns, load_closes


@pytest.fixture
def closes_csv(tmp_path):
    path = tmp_path / "closes.csv"
    path.write_text(
        "date,IVV,AGG\n"
        "2024-01-03,480.0,98.0\n"
        "2024-01-02,478.0,98.5\n"  # out of order on purpose
        "2024-01-04,484.8,97.5\n"
    )
    return path


def test_load_closes_parses_and_sorts_dates(closes_csv):
    closes = load_closes(closes_csv)
    assert list(closes.columns) == ["IVV", "AGG"]
    assert closes.index.is_monotonic_increasing
    assert closes.index[0] == pd.Timestamp("2024-01-02")
    assert closes.loc["2024-01-03", "IVV"] == pytest.approx(480.0)


def test_daily_returns_by_hand(closes_csv):
    returns = daily_returns(load_closes(closes_csv))
    # 478 → 480 is +0.4184%, 480 → 484.8 is exactly +1%.
    assert returns.loc["2024-01-03", "IVV"] == pytest.approx(480.0 / 478.0 - 1)
    assert returns.loc["2024-01-04", "IVV"] == pytest.approx(0.01)
    # The first day has no prior close and is dropped.
    assert pd.Timestamp("2024-01-02") not in returns.index
