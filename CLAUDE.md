# Client Portfolio Builder

A client portfolio construction tool for a private wealth analyst.
Starts from a client profile, not a market signal.

## Rules
- Every method must be explainable to a banker in one sentence.
- No optimizers, no Black-Litterman, no machine learning, no factor models.
- Python 3.11, pandas, numpy, pytest. Keep dependencies minimal.
- Package lives in src/cpb/. Tests in tests/. Example in examples/.
- Small functions, docstrings that state the rule in plain English.
- Reuse the structure of github.com/martinduran10 etf repo (pyproject, pytest, GitHub Actions CI).

## Modules, in build order
1. profile.py      ClientProfile → risk level 1-5
2. allocation.py   five model portfolios by level, 10-yr return estimates, simple valuation adjustment
3. implementation.py  asset class → ETF, weights → holdings
4. stress.py       2008/2020/2022, max drawdown, Monte Carlo goal-miss probability
5. fx.py           local-currency slice for a LATAM client
6. proposal.py     one-page HTML/PDF

## Worked example
A family based in Bogotá: $5M, 60% offshore in Miami, 15-year horizon,
goal "grow", tolerates a 15% loss in a bad year, COP exposure on the onshore 40%.

## Data
Bloomberg daily closes for 43 ETFs in data/ (not committed; loader reads a CSV path).
