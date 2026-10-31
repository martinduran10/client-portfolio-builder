"""The committed proxy cache loads cleanly and covers the stress episodes."""

import pandas as pd
import pytest

from cpb.allocation import ASSET_CLASSES
from cpb.proxies import (
    PROXIES_CSV,
    PROXY_MAP,
    PROXY_TICKERS,
    common_closes,
    common_window,
    load_proxies,
    monthly_returns,
)


@pytest.fixture(scope="module")
def closes():
    return load_proxies()


class TestCache:
    def test_cache_is_committed_and_has_every_ticker(self, closes):
        assert PROXIES_CSV.exists()
        assert list(closes.columns) == list(PROXY_TICKERS)

    def test_month_end_index_is_sorted_and_unique(self, closes):
        assert closes.index.is_monotonic_increasing
        assert closes.index.is_unique
        assert (closes.index == closes.index + pd.offsets.MonthEnd(0)).all()

    def test_history_spans_the_three_episodes(self, closes):
        assert closes.index[0] <= pd.Timestamp("2007-09-30")
        assert closes.index[-1] >= pd.Timestamp("2022-12-31")

    def test_every_model_asset_class_has_a_proxy(self):
        assert set(PROXY_MAP) == set(ASSET_CLASSES)
        assert set(PROXY_MAP.values()) <= set(PROXY_TICKERS)


class TestWindows:
    def test_common_window_starts_when_the_youngest_proxy_lists(self, closes):
        start, end = common_window(closes)
        assert start == pd.Timestamp("2007-05-31")  # BIL's first month-end
        assert end == closes.index[-1]

    def test_common_closes_have_no_gaps(self, closes):
        full = common_closes(closes)
        assert not full.isna().any().any()
        assert len(full) >= 200  # well over sixteen years of month-ends

    def test_monthly_returns_drop_the_first_row(self, closes):
        rets = monthly_returns(closes)
        assert len(rets) == len(closes) - 1
        # 2008 was a down year for SPY under any reasonable data.
        assert (1 + rets.loc["2008", "SPY"]).prod() - 1 < -0.30
