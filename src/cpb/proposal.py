"""One-page proposal the banker can print or save as PDF.

The page is self-contained HTML with print CSS sized to a single A4
sheet; any browser's "Print → Save as PDF" turns it into the PDF, so
no PDF library is needed.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from .allocation import MODEL_NAMES
from .implementation import ETF_NAMES
from .profile import ClientProfile, fits_tolerance, worst_year_loss

_CSS = """
@page { size: A4; margin: 18mm; }
body { font-family: Georgia, 'Times New Roman', serif; color: #1a1a2e;
       max-width: 760px; margin: 2em auto; line-height: 1.45; }
h1 { font-size: 1.5em; border-bottom: 2px solid #1a1a2e; padding-bottom: 6px; }
h2 { font-size: 1.05em; margin-top: 1.4em; text-transform: uppercase;
     letter-spacing: 0.06em; color: #444; }
table { border-collapse: collapse; width: 100%; margin: 0.6em 0; }
th, td { text-align: left; padding: 4px 10px 4px 0; border-bottom: 1px solid #ddd;
         font-size: 0.95em; }
th { font-weight: 600; color: #444; }
td.num, th.num { text-align: right; }
.meta { color: #555; font-size: 0.9em; }
.neg { color: #8b0000; }
.footer { margin-top: 2em; font-size: 0.75em; color: #777;
          border-top: 1px solid #ccc; padding-top: 6px; }
"""


def _pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"


def _usd(x: float) -> str:
    return f"${x:,.0f}"


def _sign(x: float) -> str:
    return "neg" if x < 0 else ""


def _window(row: pd.Series) -> str:
    start = pd.Timestamp(row.window_start).strftime("%b %Y")
    end = pd.Timestamp(row.window_end).strftime("%b %Y")
    return f"{start}–{end}"


def render_proposal(
    profile: ClientProfile,
    level: int,
    holdings: pd.DataFrame,
    expected_return: float,
    scenarios: pd.DataFrame,
    drawdown: dict[str, object],
    target_usd: float,
    miss_probability: float,
    n_paths: int,
    tradeoff: pd.DataFrame,
    fx: dict[str, float] | None = None,
    as_of: date | None = None,
) -> str:
    """Build the one-page HTML proposal from the pieces the other modules made.

    ``scenarios`` is the table from ``stress.replay_scenarios``: one row
    per episode with its calendar-year return and peak-to-trough slide.
    ``drawdown`` is ``stress.historical_drawdown`` for the same mix.
    ``expected_return`` is the number the Monte Carlo used and ``n_paths``
    how many futures it drew.  ``tradeoff`` is ``tradeoff.tradeoff_table``:
    the recommended level and the next one up.  ``fx``, when given, carries ``onshore_usd``,
    ``offshore_usd`` and the ``depreciation`` used for the currency stress
    line; the onshore slice carries no expected currency drift.
    """
    as_of = as_of or date.today()

    holding_rows = "\n".join(
        f"<tr><td>{row.ticker}</td><td>{ETF_NAMES.get(row.ticker, row.asset_class)}</td>"
        f"<td class='num'>{_pct(row.weight, 0)}</td>"
        f"<td class='num'>{_usd(row.amount_usd)}</td></tr>"
        for row in holdings.itertuples()
    )

    scenario_rows = "\n".join(
        f"<tr><td>{name} <span class='meta'>({_window(row)})</span></td>"
        f"<td class='num {_sign(row.calendar_year_return)}'>{_pct(row.calendar_year_return)}</td>"
        f"<td class='num {_sign(row.peak_to_trough)}'>{_pct(row.peak_to_trough)}</td>"
        f"<td class='num'>{_usd(profile.total_assets_usd * row.peak_to_trough)}</td></tr>"
        for name, row in scenarios.iterrows()
    )

    tolerance = _pct(profile.max_annual_loss, 0)
    if not fits_tolerance(profile.max_annual_loss):
        band_note = (
            f"No model portfolio fits the stated {tolerance} bad-year tolerance: even "
            f"the most conservative mix lost {_pct(worst_year_loss(1), 0)} in its worst "
            f"replayed calendar year (2008, 2020 or 2022), so level 1 is shown. "
        )
    else:
        next_up = (
            f"; the next level up lost {_pct(worst_year_loss(level + 1), 0)}. "
            if level < 5 else ". "
        )
        band_note = (
            f"A level is held only if its worst replayed calendar year (2008, 2020 or "
            f"2022) stays inside the client's tolerance: this mix lost "
            f"{_pct(worst_year_loss(level), 0)} in its worst year, within the {tolerance} "
            f"the client can sit through{next_up}"
        )
    crisis = "2008 global financial crisis"
    crisis_note = (
        f"In a crisis like 2008, this portfolio fell "
        f"{_pct(-scenarios.loc[crisis, 'peak_to_trough'])} from peak to trough."
        if crisis in scenarios.index else ""
    )

    def _role(lvl: int) -> str:
        return "recommended" if lvl == level else "next level up"

    tradeoff_rows = "\n".join(
        f"<tr><td>Level {lvl} — {row['name']} <span class='meta'>({_role(lvl)})</span></td>"
        f"<td class='num {_sign(row.worst_year_return)}'>{_pct(row.worst_year_return)} "
        f"<span class='meta'>({row.worst_year})</span></td>"
        f"<td class='num {_sign(row.crisis_2008_slide)}'>{_pct(row.crisis_2008_slide)}</td>"
        f"<td class='num'>{_pct(row.expected_return)}</td>"
        f"<td class='num'>{_pct(row.miss_probability, 0)}</td></tr>"
        for lvl, row in tradeoff.iterrows()
    )

    dd_start = pd.Timestamp(drawdown["window_start"]).strftime("%b %Y")
    dd_end = pd.Timestamp(drawdown["window_end"]).strftime("%b %Y")
    dd = float(drawdown["max_drawdown"])

    fx_section = ""
    if fx is not None:
        hit = -fx["onshore_usd"] / profile.total_assets_usd * fx["depreciation"]
        fx_section = f"""
<h2>Currency ({profile.local_currency})</h2>
<p>{_usd(fx['offshore_usd'])} is held offshore in USD and
{_usd(fx['onshore_usd'])} onshore in {profile.local_currency}.
If the {profile.local_currency} weakened {_pct(fx['depreciation'], 0)},
the whole portfolio would be worth about {_pct(hit)} less in dollars
({_usd(profile.total_assets_usd * hit)}). No currency drift is built into
the return estimate: the extra interest the {profile.local_currency} pays
is expected to offset its slide.</p>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Portfolio proposal — {profile.name}</title>
<style>{_CSS}</style>
</head>
<body>
<h1>Portfolio proposal — {profile.name}</h1>
<p class="meta">Prepared {as_of.isoformat()} · {_usd(profile.total_assets_usd)} ·
{profile.horizon_years:.0f}-year horizon · goal: {profile.goal}</p>

<h2>Risk level</h2>
<p>Level {level} of 5 — {MODEL_NAMES[level]}. This is the most conservative of
what the client's stated tolerance for a {_pct(profile.max_annual_loss, 0)}
bad-year loss, the {profile.horizon_years:.0f}-year horizon, and the
"{profile.goal}" goal each allow.</p>
<p>{band_note}{crisis_note}</p>

<h2>Recommended portfolio</h2>
<table>
<tr><th>Ticker</th><th>Fund</th><th class="num">Weight</th><th class="num">Amount</th></tr>
{holding_rows}
</table>
<p>Estimated return over the next ten years: <strong>{_pct(expected_return)}</strong>
a year, from long-run building blocks nudged for today's valuations.</p>

<h2>If history repeated</h2>
<table>
<tr><th>Episode</th><th class="num">Full year</th><th class="num">Peak to trough</th>
<th class="num">Peak to trough, dollars</th></tr>
{scenario_rows}
</table>
<p class="meta">Replayed on the daily history of one ETF per asset class.
"Full year" is the calendar-year return; "peak to trough" is the worst
close-to-close slide inside the window shown.</p>
<p>Worst slide of this mix on the same history, {dd_start} to {dd_end}:
<strong class="{_sign(dd)}">{_pct(dd)}</strong> peak to trough
({_usd(profile.total_assets_usd * dd)}).</p>

<h2>Odds of missing the goal</h2>
<p>Across {n_paths:,} simulated futures, this mix ends below the
{_usd(target_usd)} target in <strong>{_pct(miss_probability, 0)}</strong> of them
after {profile.horizon_years:.0f} years.</p>

<h2>Trade-off</h2>
<table>
<tr><th>Level</th><th class="num">Worst calendar year</th><th class="num">2008 peak to trough</th>
<th class="num">Expected return</th><th class="num">Odds of missing the goal</th></tr>
{tradeoff_rows}
</table>
<p>Reaching the goal with higher confidence requires accepting a larger loss in a bad year.</p>
{fx_section}
<p class="footer">Return estimates are long-run assumptions, not promises.
Scenario figures replay past episodes on daily ETF prices and do not predict
the next one.
For discussion purposes only.</p>
</body>
</html>
"""


def write_proposal(html: str, path: str | Path) -> Path:
    """Write the proposal HTML to disk, creating parent folders as needed."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    return path
