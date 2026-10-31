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
print(f"Mix return: {mu:.2%} a year over ten years (volatility {sigma:.1%})")

# --- 3. Implementation: ETFs and dollars -------------------------------------
holdings = implementation.to_holdings(weights, profile.total_assets_usd)
print("\nHoldings:")
print(holdings.to_string(index=False))

# --- 4. Stress: three bad episodes and the worst slide on record -------------
monthly = proxies.load_proxies()  # cached month-end closes of the proxy ETFs
scenarios = stress.replay_scenarios(weights, monthly)
print("\nIf history repeated (full year / peak to trough):")
for name, row in scenarios.iterrows():
    print(f"  {name}: {row.calendar_year_return:.1%} / {row.peak_to_trough:.1%} "
          f"({row.peak_to_trough * profile.total_assets_usd:,.0f} USD)")

drawdown = stress.historical_drawdown(weights, monthly)
print(f"Worst month-end slide of this mix, {drawdown['window_start']:%b %Y} to "
      f"{drawdown['window_end']:%b %Y}: {drawdown['max_drawdown']:.1%}")

closes_path = Path(__file__).resolve().parents[1] / "data" / "closes.csv"
if closes_path.exists():
    closes = data.load_closes(closes_path)
    returns = stress.portfolio_returns(implementation.ticker_weights(weights), closes)
    print(f"Worst daily slide on the Bloomberg closes: {stress.max_drawdown(returns):.1%}")

# --- 5. FX: the COP slice ----------------------------------------------------
split = fx.custody_split(profile.total_assets_usd, profile.offshore_share)
local_rate, usd_rate = 0.09, 0.04  # COP policy rate vs USD rate, rule of thumb
drift = fx.expected_depreciation(local_rate, usd_rate)
mu_usd = fx.blended_expected_return(mu, profile.onshore_share, local_rate, usd_rate)
depreciation = 0.20
hit = fx.fx_stress(profile.onshore_share, depreciation)
print(f"\nCustody: ${split['offshore_usd']:,.0f} offshore USD, "
      f"${split['onshore_usd']:,.0f} onshore COP")
print(f"Expected COP slide from the rate difference: {drift:.1%} a year")
print(f"Expected return in dollars after that slide on the onshore slice: {mu_usd:.2%}")
print(f"If COP weakens {depreciation:.0%}, the portfolio loses {hit:.1%} in USD")

# --- 6. Odds of missing the goal ---------------------------------------------
target_usd = 10_000_000  # "grow": double the money over the 15 years
n_paths = stress.DEFAULT_N_PATHS
miss = stress.goal_miss_probability(
    profile.total_assets_usd, target_usd, int(profile.horizon_years),
    mu_usd, sigma, n_paths=n_paths,
)
print(f"\nOdds of ending below ${target_usd:,.0f} in 15 years "
      f"({n_paths:,} paths): {miss:.0%}")

# --- 7. One-page proposal ----------------------------------------------------
html = render_proposal(
    profile=profile,
    level=level,
    holdings=holdings,
    expected_return=mu_usd,
    scenarios=scenarios,
    drawdown=drawdown,
    target_usd=target_usd,
    miss_probability=miss,
    n_paths=n_paths,
    fx={**split, "depreciation": depreciation,
        "expected_depreciation": drift, "mix_return": mu},
)
out = write_proposal(html, Path(__file__).parent / "output" / "bogota_family.html")
print(f"\nProposal written to {out}")
print("Open it in a browser and print to PDF for the one-pager.")
