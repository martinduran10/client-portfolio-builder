"""Client profile and the risk-level rule.

The rule in one sentence: the client's risk level is the most
conservative of three independent reads — what their stated loss
tolerance allows, what their time horizon allows, and what their goal
calls for.  We never take more risk than the client's own answers allow.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

# The most aggressive level each goal can justify on its own.
GOAL_CAPS = {"preserve": 2, "income": 3, "balanced": 4, "grow": 5}

# What each level's mix lost in its worst calendar year on the
# 2008/2020/2022 replays (data/proxies.csv month-ends, rebalanced
# monthly), rounded to the nearest whole percent.  A client must tolerate
# at least this to hold the level.  Regenerate with
# ``python -m cpb.calibrate``; tests/test_tolerance.py fails if these
# drift from the data.
WORST_YEAR_LOSS = {1: 0.09, 2: 0.12, 3: 0.21, 4: 0.30, 5: 0.38}


class ToleranceWarning(UserWarning):
    """No model portfolio's worst replayed year fits the stated tolerance."""


@dataclass(frozen=True)
class ClientProfile:
    """Everything the risk conversation produces, in one record.

    Parameters
    ----------
    name : str
        How the client appears on the proposal.
    total_assets_usd : float
        Investable assets, expressed in USD.
    horizon_years : float
        Years until the money is needed.
    goal : str
        One of ``preserve``, ``income``, ``balanced``, ``grow``.
    max_annual_loss : float
        The loss in a bad year the client says they can sit through,
        as a fraction (0.15 means "I can tolerate a 15% down year").
    offshore_share : float
        Fraction of assets held offshore in USD (the rest is onshore
        in ``local_currency``).
    local_currency : str
        Currency of the onshore slice, e.g. ``"COP"``.
    """

    name: str
    total_assets_usd: float
    horizon_years: float
    goal: str
    max_annual_loss: float
    offshore_share: float = 1.0
    local_currency: str = "USD"

    def __post_init__(self) -> None:
        if self.total_assets_usd <= 0:
            raise ValueError("total_assets_usd must be positive")
        if self.horizon_years <= 0:
            raise ValueError("horizon_years must be positive")
        if self.goal not in GOAL_CAPS:
            raise ValueError(f"goal must be one of {sorted(GOAL_CAPS)}, got {self.goal!r}")
        if not 0 < self.max_annual_loss <= 1:
            raise ValueError("max_annual_loss must be a fraction in (0, 1]")
        if not 0 <= self.offshore_share <= 1:
            raise ValueError("offshore_share must be a fraction in [0, 1]")

    @property
    def onshore_share(self) -> float:
        """Fraction of assets held onshore in the local currency."""
        return 1.0 - self.offshore_share


def worst_year_loss(level: int) -> float:
    """What the level's mix lost in its worst replayed calendar year, which
    is the smallest bad-year loss a client must tolerate to hold it:
    9% at level 1, 12% at 2, 21% at 3, 30% at 4, 38% at 5."""
    if level not in WORST_YEAR_LOSS:
        raise ValueError(f"risk level must be 1-5, got {level}")
    return WORST_YEAR_LOSS[level]


def fits_tolerance(max_annual_loss: float) -> bool:
    """Whether even the most conservative mix stayed inside the tolerance
    in its worst replayed year."""
    return worst_year_loss(1) <= max_annual_loss


def loss_tolerance_level(max_annual_loss: float) -> int:
    """Level the stated loss tolerance allows: the highest level whose worst
    replayed year stayed inside it (tolerating 9% → 1, 12% → 2, 21% → 3,
    30% → 4, 38% → 5).  If even level 1 lost more than the client can sit
    through, level 1 is assigned with a ``ToleranceWarning``.
    """
    allowed = [level for level, loss in WORST_YEAR_LOSS.items() if loss <= max_annual_loss]
    if not allowed:
        warnings.warn(
            f"no model portfolio fits a {max_annual_loss:.0%} bad-year tolerance: "
            f"even level 1 lost {worst_year_loss(1):.0%} in its worst replayed year; "
            "assigning level 1",
            ToleranceWarning,
            stacklevel=2,
        )
        return 1
    return max(allowed)


def horizon_level(horizon_years: float) -> int:
    """Level the time horizon allows: longer money can ride out more.

    Under 3 years → 1, under 5 → 2, under 10 → 3, under 15 → 4, 15+ → 5.
    """
    bands = ((3, 1), (5, 2), (10, 3), (15, 4))
    for cap, level in bands:
        if horizon_years < cap:
            return level
    return 5


def goal_level(goal: str) -> int:
    """Level the goal calls for: preserve → 2, income → 3, balanced → 4, grow → 5."""
    return GOAL_CAPS[goal]


def risk_level(profile: ClientProfile) -> int:
    """The client's risk level 1-5: the lowest of the three independent reads."""
    return min(
        loss_tolerance_level(profile.max_annual_loss),
        horizon_level(profile.horizon_years),
        goal_level(profile.goal),
    )
