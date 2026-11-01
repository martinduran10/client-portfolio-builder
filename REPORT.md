# Report: the `sourced-data` branch

Branched from `main` at `e81d350` (the SOURCES/DECISIONS audit) on
2026-10-31. Seven commits, one per step, pushed to `origin/sourced-data`.
Not merged, no pull request. Asset classes, model weights and the
risk-level rule are untouched; everything I would change there is in
the last section.

## What changed, step by step

**1. Proxy loader and cache** (`936d2c9`). New `src/cpb/proxies.py`
downloads daily adjusted closes from Yahoo Finance with `yfinance`
(1.7.0), keeps each month's last close, drops a month still in progress,
and caches the result in `data/proxies.csv` (23 KB, 406 month-ends from
1993-01 to 2026-10, eight tickers: SPY, EFA, EEM, AGG, SHY, BIL, HYG,
GLD). The cache is committed with a `.gitignore` exception; `yfinance`
is an optional `[data]` extra used only by `python -m cpb.proxies`.
Tests, CI and the example read the cache. The network was reachable, so
nothing in this step was skipped.

**2. Scenario replays** (`2145ab1`). The hand-typed per-asset-class
table in `stress.py` is gone. `replay_scenarios` returns, per episode,
the calendar-year return and the peak-to-trough slide inside the window
(Oct 2007–Feb 2009, Feb–Mar 2020, calendar 2022), computed on the
proxies' month-end history with constant weights (monthly rebalanced).
`asset_class_scenarios` gives the same two numbers per building block.
`max_drawdown` now counts a drop in the first period (it used to start
the curve after the first return, which hid a first-month fall).
`portfolio_daily_returns` became `portfolio_returns` since it works at
any frequency. The proposal's "If history repeated" table shows both
numbers per episode and labels the window.

**3. Volatility from history** (`3f1498b`). New `src/cpb/calibrate.py`
computes each mix's annualized volatility (sample standard deviation of
monthly returns × √12) over the longest window all proxies share
(returns 2007-06 to 2026-10, 232 months). `allocation.MODEL_VOLATILITY`
holds the output and a test asserts it equals the computation, so the
comment above the table is now true and enforced.

**4. Dead ends closed** (`0a2c53e`). `fx.blended_expected_return` lowers
the onshore slice's expected return by the expected COP slide and blends
by custody share; the example feeds that number to the Monte Carlo and
to the proposal, whose return line now shows the split. The proposal
takes `n_paths` and prints it (`stress.DEFAULT_N_PATHS` names the
default) instead of a hardcoded "10,000". The proposal takes a
`drawdown` dict from `stress.historical_drawdown` and prints the worst
month-end slide over the common window, so max drawdown is on the page
without the uncommitted Bloomberg file.

**5. Tolerance test** (`24ba028`). `profile.LOSS_TOLERANCE_BANDS` and
`profile.max_loss_for_level` expose the existing bands; the rule itself
is unchanged (its tests pass untouched). `tests/test_tolerance.py`
checks each level's worst replayed loss, on both measures, against its
band. Eight of ten cases breach and are marked strict xfail with the
numbers in the reason; level 5 (no cap) passes.

**6. SOURCES.md** (`cf5a7f6`). Rewritten: section 0 documents the data;
volatilities, replays and the worst slide on record are marked computed
with source, date range and method; returns, valuation, rates, the 20%
stress and the risk bands stay marked estimated.

**7. This report**, plus a README refresh and a status note at the top
of DECISIONS.md pointing at the sections this branch supersedes.

## Every number that moved

Volatility by level (`allocation.MODEL_VOLATILITY`):

| Level | Old | New |
|---|---|---|
| 1 | 4.50% | 3.75% |
| 2 | 7.00% | 6.54% |
| 3 | 9.50% | 9.44% |
| 4 | 12.00% | 12.30% |
| 5 | 14.50% | 15.20% |

Scenario figures per asset class. Old is the hand-typed single number;
new is full year / peak-to-trough on month-ends:

| Asset class | 2008 old → new | 2020 old → new | 2022 old → new |
|---|---|---|---|
| us_equity | -37% → -36.8% / -50.8% | -34% → +18.3% / -19.4% | -18% → -18.2% / -23.9% |
| intl_equity | -43% → -41.0% / -57.4% | -33% → +7.6% / -20.8% | -14% → -14.4% / -27.2% |
| em_equity | -53% → -48.9% / -60.4% | -32% → +17.0% / -19.0% | -20% → -20.6% / -29.4% |
| core_bonds | +5% → +7.9% / -4.3% | -1% → +7.5% / -0.5% | -13% → -13.0% / -15.5% |
| short_bonds | +7% → +6.6% / -1.2% | +1% → +3.0% / 0.0% | -4% → -3.9% / -4.7% |
| cash | +2% → +1.6% / -0.3% | 0% → +0.4% / 0.0% | +1.5% → +1.4% / 0.0% |

Scenario figures per model portfolio. Old is the weighted average of
the old table; new is full year / peak-to-trough:

| Level | 2008 old → new | 2020 old → new | 2022 old → new |
|---|---|---|---|
| 1 | -1.3% → -1.2% / -6.9% | -5.2% → +6.9% / -2.0% | -9.4% → -9.3% / -11.7% |
| 2 | -11.0% → -11.6% / -19.6% | -12.0% → +9.8% / -6.4% | -12.4% → -12.3% / -16.2% |
| 3 | -20.6% → -21.3% / -32.3% | -18.6% → +11.9% / -10.6% | -14.3% → -14.2% / -19.5% |
| 4 | -29.8% → -30.1% / -42.9% | -25.2% → +13.6% / -14.7% | -15.7% → -15.6% / -22.2% |
| 5 | -38.8% → -37.9% / -52.0% | -31.8% → +15.2% / -18.7% | -17.1% → -17.1% / -24.8% |

Worst slide on record (new; nothing was shown before): level 1 -11.8%,
level 2 -19.6%, level 3 -32.3%, level 4 -42.9%, level 5 -52.0%, month-end
peak to trough over 2007-05 to 2026-10.

The Bogotá example (level 3, $5M, 15 years, $10M target):

| Output | Old | New |
|---|---|---|
| Mix return before currency | 5.04% | 5.04% (unchanged) |
| Expected return fed to the Monte Carlo | 5.04% | 3.03% (after the 5% a year COP slide on the 40% onshore) |
| Volatility | 9.5% | 9.44% |
| Odds of ending below $10M | 52% | 80% |
| 2008 line on the page | -20.6% (-$1,027,500) | -21.3% full year / -32.3% peak to trough (-$1,613,428) |
| 2020 line | -18.6% (-$931,500) | +11.9% / -10.6% (-$528,988) |
| 2022 line | -14.3% (-$714,250) | -14.1% / -19.5% (-$975,132) |
| Worst slide on the page | not shown | -32.3% (May 2007 to Oct 2026) |
| Path count on the page | fixed text "10,000" | the value passed, still 10,000 |

The move from 52% to 80% comes almost entirely from the currency slide:
with the old return and the new volatility the odds are 51.9%; with the
blended return and the old volatility they are 80.2%.

## What failed or was skipped, and why

- **Nothing was skipped for lack of network.** Yahoo Finance answered;
  the cache was written on 2026-10-31.
- **Eight expected failures** in `tests/test_tolerance.py`, by design:
  levels 1-4 breach their band on both the full-year and the
  peak-to-trough measure (level 1: -9.3% / -11.7% against 5%; level 2:
  -12.3% / -19.6% against 10%; level 3: -21.3% / -32.3% against 15%;
  level 4: -30.1% / -42.9% against 25%). Strict xfail, so the suite will
  flag it if any of them starts passing. Final run: 106 passed, 8 xfailed.
- **Month-end data flattens the 2020 window.** On month-ends the
  Feb–Mar 2020 slide is -19.4% for SPY; on daily closes (checked once,
  not cached) it is -33.7%, and the other proxies read EFA -33.4%, EEM
  -31.6%, AGG -9.6%, SHY -0.7%, BIL 0.0%. The 2008 window on daily data
  reads SPY -51.4%, EFA -57.6%, EEM -66.4%, AGG -12.8%, SHY -2.2%, BIL
  -0.8%. The brief asked for a monthly loader, so I kept month-ends and
  put the caveat on the page footer and in SOURCES.md.
- **ETF price returns, not index returns.** AGG's 2008 full year is
  +7.9% on the ETF's adjusted price versus about +5% for the index; the
  hand table had +5%. Premium/discount swings are in every ETF-based
  number.
- **Replay proxies differ from the holdings.** Replays and volatility
  use SPY/EFA/EEM (long history); the holdings table still maps to
  IVV/IEFA/IEMG. Same indices, different funds.
- **The regenerated proposal is not committed.** `examples/output/` is
  gitignored from the first commit; `python examples/bogota_family.py`
  rewrites `examples/output/bogota_family.html` locally and CI runs it.
- **Refreshing the data will fail one test on purpose.** After
  `python -m cpb.proxies`, `test_table_matches_the_proxy_history` fails
  until `python -m cpb.calibrate` output is pasted into
  `allocation.MODEL_VOLATILITY`.
- **Noise only:** `yfinance` 1.7.0 emits pandas 3.1 deprecation warnings
  during a refresh. Tests and the example are warning-free.

## Decisions waiting for you

1. **Tolerance bands versus model weights.** Every capped level breaches
   its band on the replays. The choices are to loosen the bands, to
   de-risk the mixes, or to redefine "a bad year" on the page as a
   2022-type year (which still breaches at levels 1 and 2). If the bands
   were set so a level's worst full-year replay never exceeds the
   tolerance that maps to it, the thresholds would be roughly 9%, 12%,
   21% and 30%, and the Bogotá family's 15% would map to level 2
   (Conservative Income) instead of 3.
2. **Daily or monthly replays.** Keeping month-ends understates the 2020
   crash by about 14 points for equities. Caching daily closes would
   cost roughly 750 KB in the repo and give the numbers a banker expects
   for 2020.
3. **Currency volatility.** The Monte Carlo now subtracts the expected
   COP slide from the mean but still uses the mix's USD volatility. Adding
   COP/USD volatility on the 40% onshore would raise the goal-miss odds
   further.
4. **What the onshore 40% actually holds.** The blended return treats it
   as the same USD mix losing the slide, a stand-in for COP assets. A
   real onshore sleeve (TES, local equity) with its own return estimate
   is the alternative from DECISIONS.md section 5.
5. **Rates and the stress size.** 9% COP, 4% USD and the 20% stress are
   still undated estimates; they drive the biggest number on the page.
6. **Proxy versus holding tickers.** Either switch the holdings to
   SPY/EFA/EEM, or accept that replays use sister funds.
7. **Return estimates and the 15% valuation premium** remain unsourced;
   SOURCES.md names the publications to cite.
8. **Pinned or live volatility.** The table is pinned constants checked
   by a test; computing it on every call would track data refreshes
   silently instead.

---

# Follow-up: three fixes (2026-11-01)

Three more commits on `sourced-data`, one per fix, then this append.
Final run: 121 passed, 0 expected failures. The Bogotá example ran
clean and rewrote `examples/output/bogota_family.html` (still
gitignored). Not merged.

## Fix 1: no expected currency drift (`4c6b226`)

`fx.blended_expected_return` is removed. The onshore 40% is modelled in
dollars: the extra interest COP pays is expected to offset its expected
slide (interest-rate carry), so subtracting the slide alone double
counted. The return estimate and the Monte Carlo use the mix's return;
the 20% COP shock stays on the proposal as a stress line, now with a
sentence saying no drift is built into the return. `expected_depreciation`
and `usd_return_of_local_asset` remain as rules for a local-currency
asset; the example no longer passes rates. DECISIONS.md section 5
rewritten with the reason.

| Output (Bogotá, level 3) | Before | After |
|---|---|---|
| Expected return fed to the Monte Carlo | 3.03% | 5.04% |
| Odds of ending below $10M in 15 years | 80% | 52% |
| Proposal return line | "in dollars: 5.0% ... less the 5.0% a year the COP is expected to slide" | "5.0% a year, from long-run building blocks nudged for today's valuations" |
| Currency section | 20% shock | 20% shock plus "No currency drift is built into the return estimate" |

## Fix 2: peak-to-trough from daily closes (`56b0e5e`)

One download now writes `data/proxies_daily.csv` (488 KB, 8,497 trading
days, 1993-01-29 to 2026-10-30) and derives `data/proxies.csv` from it.
Peak-to-trough slides and the worst slide on record use the daily file.
Calendar-year returns stay on month-ends, as do the volatility table and
the Monte Carlo: a replayed year is the mix rebalanced monthly, which is
what the volatility is measured on. On daily closes with daily
rebalancing the 2008 full year for level 3 would read -19.5% instead of
-21.3%, a rebalancing artefact rather than a market fact, so I kept the
month-end figure for the number that sets the bands.

Re-downloading moved 321 cells of the monthly cache in the fourth
decimal (Yahoo's adjustment arithmetic); the volatility table did not
move at four decimals and its pinned test still passes.

Peak-to-trough per model portfolio, month-ends → daily:

| Level | 2008 | 2020 | 2022 | Worst on record |
|---|---|---|---|---|
| 1 | -6.9% → -11.3% | -2.0% → -7.6% | -11.7% → -12.5% | -11.8% → -12.8% |
| 2 | -19.6% → -21.0% | -6.4% → -13.7% | -16.2% → -16.7% | -19.6% → -21.0% |
| 3 | -32.3% → -32.9% | -10.6% → -19.4% | -19.5% → -20.0% | -32.3% → -33.3% |
| 4 | -42.9% → -43.3% | -14.7% → -25.8% | -22.2% → -22.7% | -42.9% → -44.8% |
| 5 | -52.0% → -52.3% | -18.7% → -31.7% | -24.8% → -25.5% | -52.0% → -54.7% |

Peak-to-trough per asset class, month-ends → daily:

| Asset class | 2008 | 2020 | 2022 |
|---|---|---|---|
| us_equity (SPY) | -50.8% → -51.4% | -19.4% → -33.7% | -23.9% → -24.5% |
| intl_equity (EFA) | -57.4% → -57.6% | -20.8% → -33.4% | -27.2% → -28.7% |
| em_equity (EEM) | -60.4% → -66.4% | -19.0% → -31.6% | -29.4% → -32.7% |
| core_bonds (AGG) | -4.3% → -12.8% | -0.5% → -9.6% | -15.5% → -16.6% |
| short_bonds (SHY) | -1.2% → -2.2% | 0.0% → -0.7% | -4.7% → -5.0% |
| cash (BIL) | -0.3% → -0.8% | 0.0% → 0.0% | 0.0% → -0.3% |

Full-year returns did not move (still month-ends). The 2008 window ends
in Feb 2009 by the brief, while the daily trough was 9 March 2009, which
is why the worst slide on record (-33.3% for level 3) is slightly deeper
than the 2008 window slide (-32.9%).

## Fix 3: loss bands calibrated to the worst replayed year (a81ecb2)

`profile.LOSS_TOLERANCE_BANDS` is now each level's worst calendar-year
replay loss rounded to the nearest whole percent, produced by
`cpb.calibrate.loss_tolerance_bands` and pinned by
`tests/test_tolerance.py`. Peak-to-trough never sets the level; the
proposal's risk section now reads, for the Bogotá family, "Loss
tolerance is matched to full calendar years: the worst year on record
for this level's mix lost 21% (replayed 2008, 2020 and 2022). In a
crisis like 2008, this portfolio fell 32.9% from peak to trough."

| Level | Band before | Worst replayed year | Band after |
|---|---|---|---|
| 1 | 5% | -9.34% (2022) | 9% |
| 2 | 10% | -12.25% (2022) | 12% |
| 3 | 15% | -21.34% (2008) | 21% |
| 4 | 25% | -30.08% (2008) | 30% |
| 5 | no cap | -37.89% (2008) | no cap |

The rule (minimum of the three reads, inclusive bands) is unchanged.
The Bogotá family's 15% tolerance maps to level 3 under both tables, so
the example's level, mix, holdings, return and odds are unchanged by
this fix; only the band sentence and the 2008 sentence were added to the
page. `tests/test_profile.py` band assertions moved to the new values.
Test count: 111 passed + 8 xfailed → 121 passed, 0 xfailed.

## Decisions still waiting for you

1. **Band direction.** With upper bounds equal to each level's worst
   year, a client tolerating 13% lands at level 3, whose worst year was
   -21%; only a client at the top of a band is fully covered. The
   conservative alternative is to require tolerance ≥ the level's worst
   year (thresholds 9/12/21/30 become the floors of levels 1-4), under
   which the Bogotá family would be level 2.
2. **Rebalancing frequency.** Calendar years use monthly rebalancing,
   slides use daily; a single convention would need either a
   monthly-rebalanced daily series or daily-rebalanced years.
3. **2008 window end.** Ending in Feb 2009 misses the 9 March 2009
   trough by about half a point at level 3; extending the window to
   Mar 2009 would align the 2008 slide with the worst on record.
4. Items 3 to 8 of the earlier list stand: currency volatility, a real
   onshore sleeve, undated rates and stress size, proxy versus holding
   tickers, unsourced return estimates and premium, pinned versus live
   tables.
