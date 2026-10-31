# Sources of every numeric assumption

Inventory as of the `sourced-data` branch (2026-10-31). Numbers fall in
two groups:

- **Computed from data**: derived from `data/proxies.csv`, the cached
  Yahoo Finance history described in section 0. Source, date range and
  method are given with each table, and a test fails if the constants
  drift from the data.
- **Estimated by the author**: still typed in by hand with no
  publication behind them. The "What it stands for" column says what a
  future revision would look up.

## 0. The data behind the computed numbers

| Item | Value |
|---|---|
| File | `data/proxies.csv` (committed, 23 KB) |
| Source | Yahoo Finance adjusted close (dividends and splits reinvested), fetched with `yfinance` 1.7.0 on 2026-10-31 |
| Granularity | daily closes resampled to each month's last close; a month still in progress is dropped |
| Span | 1993-01 to 2026-10 (406 month-ends); SPY starts 1993-01, EFA 2001-08, EEM 2003-04, AGG 2003-09, SHY 2002-07, BIL 2007-05, HYG 2007-04, GLD 2004-11 |
| Longest common window | month-ends 2007-05-31 to 2026-10-31, i.e. 232 monthly returns from 2007-06 to 2026-10 (BIL is the youngest proxy) |
| Proxies | us_equity → SPY, intl_equity → EFA, em_equity → EEM, core_bonds → AGG, short_bonds → SHY, cash → BIL (`cpb.proxies.PROXY_MAP`); HYG and GLD are cached for future classes and unused |
| Refresh | `pip install -e ".[data]"` then `python -m cpb.proxies` (network needed) |

Two caveats carry through every computed number. ETF prices include
premium/discount swings the underlying index does not have (AGG's 2008
return of +7.9% below is a price return; the Bloomberg US Aggregate
index itself returned about +5%). And month-end data cannot see a slide
that starts and ends inside a month: on daily closes the Feb–Mar 2020
peak-to-trough for SPY was about -34%, on month-ends it is -19%.

Note that the replays use SPY/EFA/EEM while the holdings table maps the
same classes to IVV/IEFA/IEMG. The pairs track the same indices; the
proxies were chosen for their longer history.

## 1. Ten-year return estimates per asset class — estimated

Annual, nominal, in USD, before the valuation nudge. Defined in
`src/cpb/allocation.py` (`TEN_YEAR_RETURNS`); used by
`allocation.expected_return`, by `examples/bogota_family.py`, and
through `fx.blended_expected_return` by `stress.goal_miss_probability`.

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

## 2. Model portfolio weights — estimated; volatilities — computed

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

**Annual volatility by level** (`MODEL_VOLATILITY`), computed from data:

| Level | Value | Source | Method |
|---|---|---|---|
| 1 | 3.75% | `data/proxies.csv`, monthly returns 2007-06 to 2026-10 | standard deviation (sample, ddof=1) of the mix's monthly returns with constant weights (rebalanced monthly), times √12 |
| 2 | 6.54% | same | same |
| 3 | 9.44% | same | same |
| 4 | 12.30% | same | same |
| 5 | 15.20% | same | same |

Produced by `python -m cpb.calibrate` (`cpb.calibrate.model_volatilities`),
rounded to four decimals. `tests/test_allocation.py` asserts the
constants equal that computation, so a data refresh that moves them
fails the suite until the table is regenerated.

## 3. Valuation adjustment and the CAPE long-run average — estimated

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

## 4. Scenario replays (2008 / 2020 / 2022) — computed

Defined in `src/cpb/stress.py` (`SCENARIO_WINDOWS`, `replay_scenarios`,
`asset_class_scenarios`); used by the example, the proposal page,
`tests/test_stress.py` and `tests/test_tolerance.py`.

| Episode | Calendar year | Peak-to-trough window (month-ends, inclusive) |
|---|---|---|
| 2008 global financial crisis | 2008 | Oct 2007 to Feb 2009, measured from the Sep 2007 month-end |
| 2020 covid crash | 2020 | Feb 2020 to Mar 2020, measured from the Jan 2020 month-end |
| 2022 rate shock | 2022 | Jan 2022 to Dec 2022, measured from the Dec 2021 month-end |

The window definitions are the author's choice (the brief's wording);
the returns inside them are computed. Method: monthly returns from the
proxy closes; the calendar-year return compounds the twelve months of
that year; the peak-to-trough is the worst slide of the growth-of-a-
dollar curve inside the window, counting the starting dollar. A model
portfolio's series is the weighted average of the proxies' monthly
returns with constant weights (rebalanced monthly).

Per asset class, from `data/proxies.csv` (Yahoo Finance adjusted
month-end closes, fetched 2026-10-31):

| Asset class (proxy) | 2008 full year | 2008 peak-to-trough | 2020 full year | 2020 peak-to-trough | 2022 full year | 2022 peak-to-trough |
|---|---|---|---|---|---|---|
| us_equity (SPY) | -36.8% | -50.8% | +18.3% | -19.4% | -18.2% | -23.9% |
| intl_equity (EFA) | -41.0% | -57.4% | +7.6% | -20.8% | -14.4% | -27.2% |
| em_equity (EEM) | -48.9% | -60.4% | +17.0% | -19.0% | -20.6% | -29.4% |
| core_bonds (AGG) | +7.9% | -4.3% | +7.5% | -0.5% | -13.0% | -15.5% |
| short_bonds (SHY) | +6.6% | -1.2% | +3.0% | 0.0% | -3.9% | -4.7% |
| cash (BIL) | +1.6% | -0.3% | +0.4% | 0.0% | +1.4% | 0.0% |

Per model portfolio (the numbers on the proposal page):

| Level | 2008 full year | 2008 peak-to-trough | 2020 full year | 2020 peak-to-trough | 2022 full year | 2022 peak-to-trough |
|---|---|---|---|---|---|---|
| 1 | -1.2% | -6.9% | +6.9% | -2.0% | -9.3% | -11.7% |
| 2 | -11.6% | -19.6% | +9.8% | -6.4% | -12.3% | -16.2% |
| 3 | -21.3% | -32.3% | +11.9% | -10.6% | -14.2% | -19.5% |
| 4 | -30.1% | -42.9% | +13.6% | -14.7% | -15.6% | -22.2% |
| 5 | -37.9% | -52.0% | +15.2% | -18.7% | -17.1% | -24.8% |

The hand-typed table these replace (2008: -37/-43/-53/+5/+7/+2; 2020:
-34/-33/-32/-1/+1/0; 2022: -18/-14/-20/-13/-4/+1.5) matched the 2008
and 2022 calendar years to within a few points but described 2020 as a
daily peak-to-trough, which month-end data cannot reproduce.

**Worst slide on record** (`stress.historical_drawdown`, shown on the
proposal page): the worst month-end peak-to-trough of the mix over the
common window 2007-05 to 2026-10. Level 1 -11.8%, level 2 -19.6%,
level 3 -32.3%, level 4 -42.9%, level 5 -52.0%. For levels 2-5 that is
the 2008 slide; for level 1 it is the 2021-2022 bond slide.

## 5. FX: rate differential and depreciation — estimated

Rules in `src/cpb/fx.py`; the numbers are set in
`examples/bogota_family.py` and repeated in `tests/test_fx.py`.

| Assumption | Value | Source | Used in |
|---|---|---|---|
| Expected depreciation rule | local rate minus USD rate, per year | Estimated by the author (uncovered interest parity stated as a rule of thumb) | `fx.expected_depreciation`, `fx.usd_return_of_local_asset` |
| Local (COP) rate | 9.0% | Estimated by the author, undated | example (`local_rate`) |
| USD rate | 4.0% | Estimated by the author, undated | example (`usd_rate`) |
| Resulting expected COP slide | 5.0% a year | Derived from the two rates above | `fx.blended_expected_return`: lowers the onshore slice's expected return, which feeds the Monte Carlo and the proposal's return line |
| Blended return rule | mix return − onshore share × expected slide | Estimated by the author | `fx.blended_expected_return` |
| COP stress depreciation | 20% | Estimated by the author | example (`depreciation`), proposal currency section |
| FX stress rule | portfolio loss = depreciation × onshore share | Estimated by the author | `fx.fx_stress`, `proposal.render_proposal` |
| Onshore share in the worked example | 40% (60% offshore) | CLAUDE.md worked example | `ClientProfile.offshore_share` |

The 9% and 4% stand in for the Banco de la República policy rate and
the US federal funds rate on the proposal date. They are not pulled from
any source and carry no date. The volatility fed to the Monte Carlo is
still the mix's USD volatility; no currency volatility is added for the
onshore slice.

## 6. Monte Carlo parameters

Defined in `src/cpb/stress.py` (`goal_miss_probability`,
`DEFAULT_N_PATHS`); inputs come from `allocation`, `fx` and the example.

| Parameter | Value | Source | Used in |
|---|---|---|---|
| Number of paths | 10,000 | Estimated by the author | `DEFAULT_N_PATHS`; the example passes the same value to the proposal, which prints it |
| Random seed | 42 | Author's choice (reproducibility) | `seed` default |
| Return distribution | normal, independent annual draws | Estimated by the author | `rng.normal(...)` |
| Mean of the draws | the blended dollar return: section 1 and 3, less the onshore share times the section 5 slide | Computed from the inputs above | `expected_return` argument |
| Standard deviation of the draws | the level's volatility | Section 2 (computed from data) | `volatility` argument |
| Worst possible year | -100% (growth factor floored at 0) | Author's choice | `np.maximum(1.0 + annual, 0.0)` |
| Time step | one year; the horizon is truncated to an integer | Author's choice | `int(horizon_years)` |
| Fees, taxes, inflation, contributions, withdrawals | none (all 0) | Author's choice | implicit |
| Goal in the worked example | $10,000,000 (double $5M in 15 years) | Estimated by the author as the meaning of "grow" | example (`target_usd`) |

## 7. Risk-level bands — estimated

Defined in `src/cpb/profile.py`; used by `profile.risk_level`.

| Assumption | Value | Source | Used in |
|---|---|---|---|
| Loss-tolerance bands | ≤5% → 1, ≤10% → 2, ≤15% → 3, ≤25% → 4, more → 5 | Estimated by the author | `LOSS_TOLERANCE_BANDS`, `loss_tolerance_level`, `max_loss_for_level` |
| Horizon bands | <3 y → 1, <5 → 2, <10 → 3, <15 → 4, 15+ → 5 | Estimated by the author | `horizon_level` |
| Goal caps | preserve 2, income 3, balanced 4, grow 5 | Estimated by the author | `GOAL_CAPS`, `goal_level` |
| Combination rule | minimum of the three | Estimated by the author | `risk_level` |

`tests/test_tolerance.py` compares each level's worst replayed loss
(section 4) with its band. Levels 1-4 breach on both the full-year and
the peak-to-trough measure; those cases are marked expected-to-fail
with the numbers, and REPORT.md carries the decision.

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
| Price rounding in the cache | four decimals | `proxies.download_monthly_closes` |
| Page size | A4, 18 mm margins | `proposal._CSS` |

## Where the remaining estimates would come from

- **Ten-year returns:** an annual capital-market assumptions
  publication (for example J.P. Morgan's Long-Term Capital Market
  Assumptions, Vanguard's Economic and Market Outlook, or BlackRock's
  Capital Market Assumptions), cited with its edition year.
- **CAPE and its long-run average:** Robert Shiller's online data
  (Yale), cited with the month of the download.
- **Rates:** Banco de la República (policy rate) and the Federal Reserve
  (federal funds target), each with the date observed.
- **COP stress size:** the historical COP/USD drawdowns over 2014-2016
  and 2020, from Banco de la República or Bloomberg.
- **Index-level scenario checks:** factsheets or Bloomberg total-return
  history for the S&P 500, MSCI EAFE, MSCI EM, Bloomberg US Aggregate,
  Bloomberg US Treasury 1-3 Year and 3-month T-bills, to confirm the
  ETF-based replays above.
