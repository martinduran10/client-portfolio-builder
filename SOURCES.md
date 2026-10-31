# Sources of every numeric assumption

Inventory as of commit `72b4f95` (2026-10-31). None of the numbers below
were taken from a publication when the code was written; every one is
**estimated by the author**. The "What it stands for" column says what a
future revision would need to look up to replace the estimate with a
sourced figure. The last section lists the natural publications to cite.

## 1. Ten-year return estimates per asset class

Annual, nominal, in USD, before the valuation nudge. Defined in
`src/cpb/allocation.py` (`TEN_YEAR_RETURNS`); used by
`allocation.expected_return`, by `examples/bogota_family.py`, and
through it by `stress.goal_miss_probability`.

| Asset class | Value | Source | What it stands for |
|---|---|---|---|
| us_equity | 6.5% | Estimated by the author | US large-cap total return (S&P 500 / IVV) |
| intl_equity | 7.0% | Estimated by the author | Developed ex-US total return in USD (MSCI EAFE / IEFA) |
| em_equity | 7.5% | Estimated by the author | Emerging-market total return in USD (MSCI EM / IEMG) |
| core_bonds | 4.0% | Estimated by the author | US investment-grade aggregate (Bloomberg US Agg / AGG) |
| short_bonds | 3.5% | Estimated by the author | 1-3 year Treasuries (SHY) |
| cash | 3.0% | Estimated by the author | 1-3 month T-bills (BIL) |

The module docstring calls these "income plus growth" building blocks,
but no income or growth components are recorded anywhere in the repo;
only the totals exist.

## 2. Model portfolio weights and volatilities

Defined in `src/cpb/allocation.py`; used by `allocation.model_portfolio`,
`allocation.expected_volatility`, and every downstream module.

| Assumption | Value | Source | Used in |
|---|---|---|---|
| Equity share by level 1-5 | 15% / 35% / 55% / 75% / 95% | Estimated by the author | `MODEL_PORTFOLIOS` |
| Level 1 mix | US 10, intl 5, EM 0, core 45, short 30, cash 10 | Estimated by the author | `MODEL_PORTFOLIOS[1]` |
| Level 2 mix | US 20, intl 10, EM 5, core 45, short 15, cash 5 | Estimated by the author | `MODEL_PORTFOLIOS[2]` |
| Level 3 mix | US 30, intl 15, EM 10, core 35, short 7, cash 3 | Estimated by the author | `MODEL_PORTFOLIOS[3]` |
| Level 4 mix | US 42, intl 20, EM 13, core 20, short 3, cash 2 | Estimated by the author | `MODEL_PORTFOLIOS[4]` |
| Level 5 mix | US 55, intl 25, EM 15, core 5, short 0, cash 0 | Estimated by the author | `MODEL_PORTFOLIOS[5]` |
| Annual volatility by level 1-5 | 4.5% / 7.0% / 9.5% / 12.0% / 14.5% | Estimated by the author | `MODEL_VOLATILITY`, fed to the Monte Carlo |

The comment above `MODEL_VOLATILITY` says the figures were "estimated from
the history of that mix". Nothing in the repo computes them, and the
Bloomberg closes are not committed, so they must be treated as unsourced
until that calculation is checked in.

## 3. Valuation adjustment and the CAPE long-run average

Defined in `src/cpb/allocation.py` (`valuation_adjustment`,
`MAX_VALUATION_ADJUSTMENT`); the premium input is set in
`examples/bogota_family.py`.

| Assumption | Value | Source | Used in |
|---|---|---|---|
| Mean-reversion speed | one tenth of the premium per year (premium / 10) | Estimated by the author | `allocation.valuation_adjustment` |
| Cap on the annual nudge | ±2.0% a year | Estimated by the author | `MAX_VALUATION_ADJUSTMENT` |
| Reference valuation | the asset's own 10-year average | Estimated by the author (rule only; no average is computed) | docstring of `valuation_adjustment` |
| US equity premium in the worked example | 15% above its 10-year average | Estimated by the author, undated | `examples/bogota_family.py` (`valuation_premiums`) |

**There is no CAPE long-run average in the repo.** The code never
computes a cyclically adjusted P/E, and no long-run mean (for example the
Shiller series average) appears anywhere. The valuation input is a
premium that the caller passes in by hand, relative to "the asset's own
10-year average valuation", and the only value ever passed is the 15%
for US equity in the example. Neither the 10-year average nor the 15%
premium is dated or sourced. Other asset classes get a 0% premium by
default, which is itself an assumption that they trade at fair value.

## 4. Scenario returns per asset class (2008 / 2020 / 2022)

Defined in `src/cpb/stress.py` (`SCENARIOS`); used by
`stress.scenario_return`, `stress.run_scenarios`, the example, the
proposal page, and `tests/test_stress.py`.

| Scenario | us_equity | intl_equity | em_equity | core_bonds | short_bonds | cash | Source |
|---|---|---|---|---|---|---|---|
| 2008 global financial crisis | -37% | -43% | -53% | +5% | +7% | +2% | Estimated by the author |
| 2020 covid crash | -34% | -33% | -32% | -1% | +1% | 0% | Estimated by the author |
| 2022 rate shock | -18% | -14% | -20% | -13% | -4% | +1.5% | Estimated by the author |

What each row stands for, from the comments in `stress.py`:

- **2008** is a calendar-year figure for each index (S&P 500, MSCI EAFE
  in USD, MSCI EM in USD, Bloomberg US Aggregate, 1-3 year Treasuries,
  3-month T-bills).
- **2020** is the roughly five-week peak-to-trough slide of
  February–March 2020, not the calendar year (which ended positive).
- **2022** is a calendar-year figure.

The rows therefore mix two period definitions (a full year versus a
peak-to-trough window). None of the eighteen figures was checked against
the Bloomberg closes in `data/`, and two of the mapped ETFs (IEFA and
IEMG) did not exist in 2008, so a data-based check would need the
underlying indices or older proxies.

## 5. FX: rate differential and depreciation

Rules in `src/cpb/fx.py`; the numbers are set in
`examples/bogota_family.py` and repeated in `tests/test_fx.py`.

| Assumption | Value | Source | Used in |
|---|---|---|---|
| Expected depreciation rule | local rate minus USD rate, per year | Estimated by the author (uncovered interest parity stated as a rule of thumb) | `fx.expected_depreciation`, `fx.usd_return_of_local_asset` |
| Local (COP) rate | 9.0% | Estimated by the author, undated | example (`local_rate=0.09`) |
| USD rate | 4.0% | Estimated by the author, undated | example (`usd_rate=0.04`) |
| Resulting expected COP slide | 5.0% a year | Derived from the two rates above | example output only; not used in the return estimate or the Monte Carlo |
| COP stress depreciation | 20% | Estimated by the author | example (`depreciation = 0.20`), proposal currency section |
| FX stress rule | portfolio loss = depreciation × onshore share | Estimated by the author | `fx.fx_stress`, `proposal.render_proposal` |
| Onshore share in the worked example | 40% (60% offshore) | CLAUDE.md worked example | `ClientProfile.offshore_share` |

The 9% and 4% stand in for the Banco de la República policy rate and
the US federal funds rate on the proposal date. They are not pulled from
any source and carry no date. The expected 5% slide is printed by the
example but never flows into the return estimate or the goal-miss odds;
only the 20% stress reaches the proposal page.

## 6. Monte Carlo parameters

Defined in `src/cpb/stress.py` (`goal_miss_probability`); inputs come
from `allocation` and the example.

| Parameter | Value | Source | Used in |
|---|---|---|---|
| Number of paths | 10,000 | Estimated by the author | `n_paths` default |
| Random seed | 42 | Author's choice (reproducibility) | `seed` default |
| Return distribution | normal, independent annual draws | Estimated by the author | `rng.normal(...)` |
| Mean of the draws | the 10-year return estimate after the valuation nudge | Section 1 and 3 | `expected_return` argument |
| Standard deviation of the draws | the level's volatility | Section 2 | `volatility` argument |
| Worst possible year | -100% (growth factor floored at 0) | Author's choice | `np.maximum(1.0 + annual, 0.0)` |
| Time step | one year; the horizon is truncated to an integer | Author's choice | `int(horizon_years)` |
| Fees, taxes, inflation, contributions, withdrawals | none (all 0) | Author's choice | implicit |
| Goal in the worked example | $10,000,000 (double $5M in 15 years) | Estimated by the author as the meaning of "grow" | example (`target_usd`) |

The proposal page prints the phrase "10,000 simulated futures" as fixed
text in `src/cpb/proposal.py`. It does not read `n_paths`, so a caller
who changes the path count will get a page that still says 10,000.

## 7. Risk-level bands

Defined in `src/cpb/profile.py`; used by `profile.risk_level`.

| Assumption | Value | Source | Used in |
|---|---|---|---|
| Loss-tolerance bands | ≤5% → 1, ≤10% → 2, ≤15% → 3, ≤25% → 4, more → 5 | Estimated by the author | `loss_tolerance_level` |
| Horizon bands | <3 y → 1, <5 → 2, <10 → 3, <15 → 4, 15+ → 5 | Estimated by the author | `horizon_level` |
| Goal caps | preserve 2, income 3, balanced 4, grow 5 | Estimated by the author | `GOAL_CAPS`, `goal_level` |
| Combination rule | minimum of the three | Estimated by the author | `risk_level` |

## 8. Worked-example inputs

From the CLAUDE.md worked example, used in `examples/bogota_family.py`
and `tests/test_profile.py` / `tests/test_proposal.py`: $5,000,000 of
assets, 15-year horizon, goal "grow", 15% tolerable bad-year loss, 60%
offshore. These are the brief, not estimates.

## 9. Other constants

| Constant | Value | Where |
|---|---|---|
| Weight-sum tolerance | 1e-6 | `allocation.expected_return` |
| Dollar rounding | nearest cent | `implementation.to_holdings`, `fx.custody_split` |
| Page size | A4, 18 mm margins | `proposal._CSS` |

## Where a sourced figure would come from

- **Ten-year returns and volatilities:** an annual capital-market
  assumptions publication (for example J.P. Morgan's Long-Term Capital
  Market Assumptions, Vanguard's Economic and Market Outlook, or
  BlackRock's Capital Market Assumptions), cited with its edition year.
- **CAPE and its long-run average:** Robert Shiller's online data
  (Yale), cited with the month of the download.
- **Scenario returns:** index factsheets or Bloomberg total-return
  history for S&P 500, MSCI EAFE, MSCI EM, Bloomberg US Aggregate,
  Bloomberg US Treasury 1-3 Year, and 3-month T-bills, with the exact
  date window stated per row.
- **Rates:** Banco de la República (policy rate) and the Federal Reserve
  (federal funds target), each with the date observed.
- **COP stress size:** the historical COP/USD drawdowns over 2014-2016
  and 2020, from Banco de la República or Bloomberg.
