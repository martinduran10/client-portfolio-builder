"""Volatility from history: hand-checked on synthetic closes, sane on the cache."""

import math

import pandas as pd
import pytest

from cpb.calibrate import historical_volatility, model_volatilities
from cpb.proxies import load_proxies


def test_hand_checked_on_a_two_month_alternation():
    # +2% / -2% every other month → monthly std of ~0.02 (sample ddof=1).
    idx = pd.date_range("2020-01-31", periods=25, freq="ME")
    closes = pd.DataFrame({"SPY": [100.0] * 25}, index=idx)
    level = 100.0
    for i in range(1, 25):
        level *= 1.02 if i % 2 else 0.98
        closes.iloc[i, 0] = level
    vol = historical_volatility({"us_equity": 1.0}, closes, proxy_map={"us_equity": "SPY"})
    monthly = pd.Series([0.02 if i % 2 else -0.02 for i in range(1, 25)]).std(ddof=1)
    assert vol == pytest.approx(monthly * math.sqrt(12))


def test_model_volatilities_rise_with_level_and_look_like_markets():
    vols = model_volatilities(load_proxies())
    assert list(vols) == [1, 2, 3, 4, 5]
    assert list(vols.values()) == sorted(vols.values())
    assert 0.02 < vols[1] < 0.08
    assert 0.10 < vols[5] < 0.25
