"""Worked example: a family based in Bogotá.

$5M, 60% offshore in Miami, 15-year horizon, goal "grow", tolerates a
15% loss in a bad year, COP exposure on the onshore 40%.  Runs end to
end on the committed proxy history; if ``data/closes.csv`` exists, it
also reports the mix's worst daily drawdown on the Bloomberg closes.
"""

from pathlib import Path

from cpb import allocation, data, fx, implementation, proxies, stress
from cpb.profile import ClientProfile, risk_level
from cpb.proposal import render_proposal, write_proposal

# --- 1. Profile → risk level -------------------------------------------------
profile = ClientProfile(
    name="Bogotá family",
    total_assets_usd=5_000_000,
    horizon_years=15,
    goal="grow",
    max_annual_loss=0.15,
    offshore_share=0.60,
    local_currency="COP",
)
level = risk_level(profile)
print(f"Risk level: {level} ({allocation.MODEL_NAMES[level]})")
print("  The 15% bad-year tolerance binds; horizon and goal would allow more.")

# --- 2. Allocation and the 10-year return estimate ---------------------------
weights = allocation.model_portfolio(level)
# US equities trade about 15% above their own 10-year average valuation.
valuation_premiums = {"us_equity": 0.15}
mu = allocation.expected_return(weights, valuation_premiums)
sigma = allocation.expected_volatility(level)
print(f"Expected return: {mu:.2%} a year over ten years (volatility {sigma:.1%})")

# --- 3. Implementation: ETFs and dollars -------------------------------------
holdings = implementation.to_holdings(weights, profile.total_assets_usd)
print("\nHoldings:")
print(holdings.to_string(index=False))

# --- 4. Stress: three bad episodes and the worst slide on record -------------
daily = proxies.load_daily_proxies()  # cached closes of the proxy ETFs
monthly = proxies.load_proxies()
scenarios = stress.replay_scenarios(weights, daily, monthly)
print("\nIf history repeated (full year / peak to trough):")
for name, row in scenarios.iterrows():
    print(f"  {name}: {row.calendar_year_return:.1%} / {row.peak_to_trough:.1%} "
          f"({row.peak_to_trough * profile.total_assets_usd:,.0f} USD)")

drawdown = stress.historical_drawdown(weights, daily)
print(f"Worst slide of this mix, {drawdown['window_start']:%b %Y} to "
      f"{drawdown['window_end']:%b %Y}: {drawdown['max_drawdown']:.1%}")

closes_path = Path(__file__).resolve().parents[1] / "data" / "closes.csv"
if closes_path.exists():
    closes = data.load_closes(closes_path)
    returns = stress.portfolio_returns(implementation.ticker_weights(weights), closes)
    print(f"Worst daily slide on the Bloomberg closes: {stress.max_drawdown(returns):.1%}")

# --- 5. FX: the COP slice ----------------------------------------------------
# The onshore slice is modelled in dollars with no expected currency drift:
# the extra interest COP pays is expected to offset its slide.  The
# currency shows up only as a stress.
split = fx.custody_split(profile.total_assets_usd, profile.offshore_share)
depreciation = 0.20
hit = fx.fx_stress(profile.onshore_share, depreciation)
print(f"\nCustody: ${split['offshore_usd']:,.0f} offshore USD, "
      f"${split['onshore_usd']:,.0f} onshore COP")
print(f"If COP weakens {depreciation:.0%}, the portfolio loses {hit:.1%} in USD")

# --- 6. Odds of missing the goal ---------------------------------------------
target_usd = 10_000_000  # "grow": double the money over the 15 years
n_paths = stress.DEFAULT_N_PATHS
miss = stress.goal_miss_probability(
    profile.total_assets_usd, target_usd, int(profile.horizon_years),
    mu, sigma, n_paths=n_paths,
)
print(f"\nOdds of ending below ${target_usd:,.0f} in 15 years "
      f"({n_paths:,} paths): {miss:.0%}")

# --- 7. One-page proposal ----------------------------------------------------
html = render_proposal(
    profile=profile,
    level=level,
    holdings=holdings,
    expected_return=mu,
    scenarios=scenarios,
    drawdown=drawdown,
    target_usd=target_usd,
    miss_probability=miss,
    n_paths=n_paths,
    fx={**split, "depreciation": depreciation},
)
out = write_proposal(html, Path(__file__).parent / "output" / "bogota_family.html")
print(f"\nProposal written to {out}")
print("Open it in a browser and print to PDF for the one-pager.")
