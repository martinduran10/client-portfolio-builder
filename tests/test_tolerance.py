"""A level's worst calendar-year replay loss (2008, 2020 or 2022), rounded
to the nearest whole percent, is the smallest bad-year loss a client must
tolerate to hold it.  The constants in profile.py must match the replays,
and peak-to-trough slides are deeper and only shown, never used to set the
level.
"""

import pytest

from cpb.allocation import model_portfolio
from cpb.calibrate import worst_year_losses
from cpb.profile import WORST_YEAR_LOSS, loss_tolerance_level, worst_year_loss
from cpb.proxies import load_daily_proxies, load_proxies
from cpb.stress import replay_scenarios


@pytest.fixture(scope="module")
def caches():
    return load_daily_proxies(), load_proxies()


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_constant_is_the_levels_worst_full_year_rounded_to_a_whole_percent(level, caches):
    worst = replay_scenarios(model_portfolio(level), *caches)["calendar_year_return"].min()
    assert worst_year_loss(level) == round(-float(worst), 2)


def test_constants_match_the_calibration(caches):
    assert WORST_YEAR_LOSS == worst_year_losses(*caches)


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_a_level_is_held_only_by_a_client_who_tolerates_its_worst_year(level):
    assert loss_tolerance_level(worst_year_loss(level)) == level
    if level > 1:
        assert loss_tolerance_level(worst_year_loss(level) - 0.001) == level - 1


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_peak_to_trough_is_deeper_than_the_worst_year_and_only_shown(level, caches):
    slide = replay_scenarios(model_portfolio(level), *caches)["peak_to_trough"].min()
    assert slide < -worst_year_loss(level)
