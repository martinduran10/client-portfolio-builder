# Where the implementation departs from CLAUDE.md

> **Status on the `sourced-data` branch (2026-10-31).** Section 4 is
> superseded: the scenario table is now replayed from the cached proxy
> history (see SOURCES.md section 4 and REPORT.md). Section 6 is
> resolved: the worst slide on record is on the proposal page. Section
> 5 is rewritten: the onshore money is the USD mix with no expected
> currency drift, and the currency is a stress line only. Sections 1,
> 2, 3 and 7 stand as written; the
> tolerance finding in section 2 is now measured by
> `tests/test_tolerance.py` and listed in REPORT.md.

CLAUDE.md gives one line per module and leaves the method open. Each
section below names a place where the code made a choice the brief did
not spell out, or went a different way than the brief implies, with the
alternative that was not taken. No code was changed to produce this
list; it describes the repo at commit `72b4f95`.

## 1. Asset classes: six broad buckets, one ETF each

CLAUDE.md speaks of "asset class → ETF" and of Bloomberg closes for 43
ETFs, which suggests a wider menu than the code uses. The implementation
fixes six classes (US equity, developed ex-US equity, emerging-market
equity, core US bonds, short Treasuries, cash) and maps each to a single
iShares or SPDR fund in `DEFAULT_ETF_MAP`. The choice keeps every line
of the proposal page explainable in a sentence and keeps the model
portfolios, the return table, and the scenario table all the same
width, so no module needs a number the others lack. The alternative was
to use more of the 43-ticker universe: gold, REITs, TIPS, high yield,
EM local-currency debt, and a Colombian equity or TES sleeve for the
onshore money. That would give the banker a richer story and a real
home for the COP slice, at the cost of a return estimate and three
scenario figures for every added class, each of which would be another
unsourced number (see SOURCES.md). Nothing in the code prevents a wider
map, since `to_holdings` accepts any `etf_map`, but `TEN_YEAR_RETURNS`
and `SCENARIOS` would need matching entries first.

## 2. The risk-level rule: minimum of three independent reads

CLAUDE.md says only "ClientProfile → risk level 1-5". The implementation
reads three answers separately (loss tolerance, horizon, goal), bands
each one into a level, and takes the lowest. The choice is conservative
by construction and gives the banker a one-sentence explanation of why
a client landed where they did: for the Bogotá family the 15% tolerance
binds at level 3 even though a 15-year horizon and a "grow" goal would
both allow level 5. The alternative, and the industry norm, is a
questionnaire score where points from each answer are added and the sum
is bucketed, so a long horizon can offset a cautious tolerance. Two
consequences of the minimum rule deserve a banker's attention. First,
the goal can only cap the level, never raise it, so a client who asks
to "grow" and gets "Balanced" needs that explained. Second, the
tolerance bands are not calibrated to the scenario table: the level-3
mix loses about 21% in the 2008 replay and 19% in the 2020 replay, both
beyond the 15% the family said they could sit through, and only the
2022 replay (about 14%) stays inside it. The code treats "a bad year" as
something like 2022, not 2008; the alternative was to set each band so
that the worst stored scenario for that level stays inside the
tolerance.

## 3. The valuation adjustment: a hand-entered premium, not CAPE

CLAUDE.md asks for a "simple valuation adjustment". The implementation
takes a premium per asset class that the caller supplies (how far the
asset trades above its own 10-year average valuation), shaves one tenth
of it off the return each year, and caps the nudge at ±2% a year. The
example passes 15% for US equity and nothing for the rest. The choice
keeps the module free of any external data or series: the banker can
say "stocks are 15% rich, so we take 1.5% a year off" and the arithmetic
is visible. The alternative was to compute the premium from data, most
naturally the Shiller CAPE against its long-run average (or against a
post-1990 average, which gives a much smaller premium), or to skip the
premium and use the earnings yield 1/CAPE directly as the US equity
return. That would make the adjustment reproducible and dated, at the
cost of a data download and a decision about which average is "normal".
As built, the 15% premium and the 10-year average it refers to are both
judgment inputs with no provenance, and the other five classes are
silently assumed to be fairly valued.

## 4. Stress tests: a scenario table instead of replaying the closes

CLAUDE.md lists "2008/2020/2022" next to a data section that promises
Bloomberg daily closes for 43 ETFs, which reads as replaying those
episodes on the actual price history. The implementation instead stores
one return per asset class per episode in `SCENARIOS` and multiplies by
the weights; the daily closes are used only for the max-drawdown
measure, and only when `data/closes.csv` is present. Three reasons drove
this. The closes are not committed, so the example and CI had to run
without them. Two of the mapped funds, IEFA and IEMG, launched in 2012,
so 2008 cannot be replayed from the mapped tickers at all. And a table
lets the banker read the per-class shock aloud. The alternative was to
replay fixed date windows on the closes (the 2007-2009 peak to trough,
19 February to 23 March 2020, calendar 2022), using older proxies such
as EFA and EEM where the mapped funds lack history, and to fall back to
the table only when the data is missing. The table as written also
mixes definitions: 2008 and 2022 are calendar-year figures while 2020 is
a five-week slide, and none of the eighteen numbers has been checked
against the data. A replay would fix both problems at once.

## 5. The onshore COP slice is modelled in dollars with no expected currency drift

CLAUDE.md describes "COP exposure on the onshore 40%" and an fx module
for "the local-currency slice". The implementation allocates the full
$5M across the six USD ETFs and treats the onshore 40% as a custody
split plus a currency stress: `custody_split` divides the dollars and
`fx_stress` scales a 20% COP drop by the onshore share for the proposal.
No expected depreciation is subtracted from the slice's return or from
the Monte Carlo drift. The reason is interest-rate carry: a currency
paying higher rates than the dollar is expected to weaken by roughly the
rate difference (`expected_depreciation`), so the extra interest the
onshore money earns and the slide it is expected to suffer cancel, and
the expected return in dollars is the mix's return whichever currency
the slice sits in. Subtracting the slide alone, which an earlier commit
on this branch did, double counts: it takes the depreciation without the
carry that compensates for it, and it moved the goal-miss odds from 52%
to 80% on nothing but that asymmetry. What the currency adds is risk,
not a lower expectation, and the proposal carries it as the 20% shock
line. The alternative is a real onshore sleeve (TES, local equity, COP
cash) with its own local return estimates converted at the expected
slide, which would make the carry explicit on both sides and would need
a return and scenario row for each local asset class.

## 6. Max drawdown is computed but never reaches the proposal

CLAUDE.md lists "max drawdown" among the stress outputs. The function
exists in `stress.max_drawdown`, but it depends on the uncommitted
closes, and `render_proposal` has no parameter for it, so the one-page
proposal never shows it even when the data is present. The example only
prints it to the console. The choice avoided a blank or misleading
field on the page when the data is absent, which is the CI case. The
alternative was to give the proposal an optional drawdown line that
appears when the data is there, or to approximate the drawdown from the
scenario table so the page always has one.

## 7. "HTML/PDF" became HTML plus the browser's print dialog

CLAUDE.md asks for a "one-page HTML/PDF". The implementation writes a
self-contained HTML page sized for A4 with print CSS and relies on
"Print → Save as PDF" in a browser; no PDF is produced by code. The
choice honours the "keep dependencies minimal" rule and avoids a
rendering library whose output would need checking on every CSS change.
The alternative was to add WeasyPrint or ReportLab and emit the PDF
directly so the banker receives a file rather than a page to print; it
would cost a heavy dependency and a system font configuration on CI.
