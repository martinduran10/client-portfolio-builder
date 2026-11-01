"""Each level's loss band is its own worst calendar-year replay loss,
rounded to the nearest whole percent, so the band a client lands in says
what that level's mix lost in its worst replayed year (2008, 2020 or
2022).  Peak-to-trough slides are deeper; they are shown on the proposal
and never used to set the level.
"""

import pytest

from cpb.allocation import model_portfolio
from cpb.calibrate import CAPPED_LEVELS, loss_tolerance_bands
from cpb.profile import LOSS_TOLERANCE_BANDS, max_loss_for_level
from cpb.proxies import load_daily_proxies, load_proxies
from cpb.stress import replay_scenarios


@pytest.fixture(scope="module")
def caches():
    return load_daily_proxies(), load_proxies()


@pytest.mark.parametrize("level", CAPPED_LEVELS)
def test_band_is_the_levels_worst_full_year_rounded_to_a_whole_percent(level, caches):
    worst = replay_scenarios(model_portfolio(level), *caches)["calendar_year_return"].min()
    assert max_loss_for_level(level) == round(-float(worst), 2)


def test_level_5_has_no_cap_and_the_deepest_year(caches):
    assert max_loss_for_level(5) is None
    worst = replay_scenarios(model_portfolio(5), *caches)["calendar_year_return"].min()
    assert worst < -max_loss_for_level(4)


def test_bands_match_the_calibration(caches):
    assert LOSS_TOLERANCE_BANDS == loss_tolerance_bands(*caches)


def test_bands_rise_with_level():
    caps = [cap for cap, _ in LOSS_TOLERANCE_BANDS]
    assert caps == sorted(caps) and len(set(caps)) == len(caps)


@pytest.mark.parametrize("level", CAPPED_LEVELS)
def test_peak_to_trough_is_deeper_than_the_band_and_only_shown(level, caches):
    slide = replay_scenarios(model_portfolio(level), *caches)["peak_to_trough"].min()
    assert slide < -max_loss_for_level(level)
