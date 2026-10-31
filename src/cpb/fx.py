"""The local-currency slice for a LATAM client, in dollar terms.

Three plain rules: the onshore slice is worth its USD value at today's
spot; a currency paying higher rates than the dollar is expected to
weaken by roughly the rate difference each year; and if the currency
drops X%, the portfolio drops X% times the onshore share.
"""

from __future__ import annotations


def custody_split(total_usd: float, offshore_share: float) -> dict[str, float]:
    """Dollars held offshore in USD versus onshore in the local currency."""
    if total_usd <= 0:
        raise ValueError("total_usd must be positive")
    if not 0 <= offshore_share <= 1:
        raise ValueError("offshore_share must be a fraction in [0, 1]")
    offshore = round(total_usd * offshore_share, 2)
    return {"offshore_usd": offshore, "onshore_usd": round(total_usd - offshore, 2)}


def expected_depreciation(local_rate: float, usd_rate: float) -> float:
    """Expected annual slide of the local currency: its rate minus the
    dollar rate (a currency paying 9% against 4% USD rates is expected
    to weaken about 5% a year)."""
    return local_rate - usd_rate


def usd_return_of_local_asset(
    local_return: float, local_rate: float, usd_rate: float
) -> float:
    """What a local-currency return is worth in dollars: the local return
    minus the currency's expected slide."""
    return local_return - expected_depreciation(local_rate, usd_rate)


def fx_stress(onshore_share: float, depreciation: float) -> float:
    """Portfolio hit if the local currency drops: the drop times the
    onshore share, as a negative fraction."""
    if not 0 <= onshore_share <= 1:
        raise ValueError("onshore_share must be a fraction in [0, 1]")
    if not 0 <= depreciation <= 1:
        raise ValueError("depreciation must be a fraction in [0, 1]")
    return -onshore_share * depreciation
