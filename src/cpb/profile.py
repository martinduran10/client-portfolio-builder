"""Client profile and the risk-level rule.

The rule in one sentence: the client's risk level is the most
conservative of three independent reads — what their stated loss
tolerance allows, what their time horizon allows, and what their goal
calls for.  We never take more risk than the client's own answers allow.
"""

from __future__ import annotations

from dataclasses import dataclass

# The most aggressive level each goal can justify on its own.
GOAL_CAPS = {"preserve": 2, "income": 3, "balanced": 4, "grow": 5}

# Bad-year loss a client can sit through → the level that allows.
# Anything beyond the last band is level 5.
LOSS_TOLERANCE_BANDS = ((0.05, 1), (0.10, 2), (0.15, 3), (0.25, 4))


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


def loss_tolerance_level(max_annual_loss: float) -> int:
    """Level the stated loss tolerance allows: a 1-5 band on the bad-year loss.

    Tolerating up to 5% → 1, 10% → 2, 15% → 3, 25% → 4, more → 5.
    """
    for cap, level in LOSS_TOLERANCE_BANDS:
        if max_annual_loss <= cap:
            return level
    return 5


def max_loss_for_level(level: int) -> float | None:
    """The largest bad-year loss a client at this level said they could sit
    through: 5% at level 1, 10% at 2, 15% at 3, 25% at 4; level 5 has no cap
    (returns ``None``)."""
    for cap, band_level in LOSS_TOLERANCE_BANDS:
        if band_level == level:
            return cap
    if level == 5:
        return None
    raise ValueError(f"risk level must be 1-5, got {level}")


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
