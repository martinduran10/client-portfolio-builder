"""Does each model portfolio's worst replayed loss stay inside the loss
tolerance band that maps to its level?

On the proxy history it does not, for levels 1-4, on either measure.
Those cases are marked expected-to-fail (strict) with the numbers in the
reason; the model weights and the risk-level rule are deliberately left
alone, and the decision is recorded in REPORT.md.
"""

import pytest

from cpb.allocation import model_portfolio
from cpb.profile import max_loss_for_level
from cpb.stress import replay_scenarios

CALENDAR = "calendar_year_return"
SLIDE = "peak_to_trough"


def breaches(reason: str):
    return pytest.mark.xfail(strict=True, reason=reason)


# Worst replayed loss per level, from data/proxies.csv (month-end closes,
# 2007-05 to 2026-10), versus the band a client at that level accepted.
CASES = [
    pytest.param(1, CALENDAR, marks=breaches("level 1 band 5%: worst full year -9.3% (2022)")),
    pytest.param(1, SLIDE, marks=breaches("level 1 band 5%: worst peak-to-trough -11.7% (2022)")),
    pytest.param(2, CALENDAR, marks=breaches("level 2 band 10%: worst full year -12.3% (2022)")),
    pytest.param(2, SLIDE, marks=breaches("level 2 band 10%: worst peak-to-trough -19.6% (2008)")),
    pytest.param(3, CALENDAR, marks=breaches("level 3 band 15%: worst full year -21.3% (2008)")),
    pytest.param(3, SLIDE, marks=breaches("level 3 band 15%: worst peak-to-trough -32.3% (2008)")),
    pytest.param(4, CALENDAR, marks=breaches("level 4 band 25%: worst full year -30.1% (2008)")),
    pytest.param(4, SLIDE, marks=breaches("level 4 band 25%: worst peak-to-trough -42.9% (2008)")),
    pytest.param(5, CALENDAR),  # level 5 has no cap
    pytest.param(5, SLIDE),
]


@pytest.mark.parametrize("level,measure", CASES)
def test_worst_replayed_loss_stays_inside_the_levels_band(level, measure):
    cap = max_loss_for_level(level)
    worst = float(replay_scenarios(model_portfolio(level))[measure].min())
    if cap is None:
        assert worst >= -1.0
        return
    assert worst >= -cap, (
        f"level {level}: worst {measure} {worst:.1%} breaches the {cap:.0%} band"
    )
