"""Weights become tickers and dollars; nothing is lost in translation."""

import pytest

from cpb.allocation import model_portfolio
from cpb.implementation import DEFAULT_ETF_MAP, ticker_weights, to_holdings


class TestToHoldings:
    def test_amounts_sum_to_total(self):
        holdings = to_holdings(model_portfolio(3), 5_000_000)
        assert holdings["amount_usd"].sum() == pytest.approx(5_000_000)

    def test_amount_is_weight_times_total(self):
        holdings = to_holdings({"us_equity": 0.6, "core_bonds": 0.4}, 1_000_000)
        us = holdings.loc[holdings["ticker"] == "IVV"].iloc[0]
        assert us["amount_usd"] == pytest.approx(600_000)

    def test_zero_weight_classes_are_dropped(self):
        holdings = to_holdings(model_portfolio(1), 1_000_000)  # em_equity is 0
        assert "IEMG" not in set(holdings["ticker"])

    def test_sorted_largest_first(self):
        holdings = to_holdings(model_portfolio(3), 1_000_000)
        weights = holdings["weight"].tolist()
        assert weights == sorted(weights, reverse=True)

    def test_every_model_asset_class_has_an_etf(self):
        for level in range(1, 6):
            assert set(model_portfolio(level)) <= set(DEFAULT_ETF_MAP)

    def test_custom_map_overrides_default(self):
        holdings = to_holdings(
            {"us_equity": 1.0}, 1_000_000, etf_map={"us_equity": "VOO"}
        )
        assert holdings["ticker"].tolist() == ["VOO"]

    def test_rejects_unmapped_asset_class(self):
        with pytest.raises(ValueError, match="no ETF mapped"):
            to_holdings({"crypto": 1.0}, 1_000_000)

    def test_rejects_nonpositive_total(self):
        with pytest.raises(ValueError, match="total_usd"):
            to_holdings({"us_equity": 1.0}, 0)


class TestTickerWeights:
    def test_collapses_onto_tickers(self):
        weights = ticker_weights(model_portfolio(3))
        assert weights["IVV"] == pytest.approx(0.30)
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_shared_ticker_weights_are_summed(self):
        etf_map = {"us_equity": "VT", "intl_equity": "VT"}
        weights = ticker_weights({"us_equity": 0.6, "intl_equity": 0.4}, etf_map)
        assert weights == {"VT": pytest.approx(1.0)}
