# client-portfolio-builder

A client portfolio construction tool for a private wealth analyst.
Starts from a client profile, not a market signal. Every method is
explainable to a banker in one sentence — no optimizers, no
Black-Litterman, no machine learning, no factor models.

## How it works

| Module | One sentence |
|---|---|
| `cpb.profile` | The risk level 1-5 is the most conservative of what the client's loss tolerance, horizon, and goal each allow. |
| `cpb.allocation` | Each level owns a fixed mix; the 10-year return is a weighted average of per-asset estimates, shaved a tenth of any valuation premium per year (capped at ±2%); each mix's volatility is its own monthly history, annualized. |
| `cpb.implementation` | One liquid ETF per asset class; dollars are weight times portfolio value. |
| `cpb.stress` | Replay 2008/2020/2022 on the mix's month-end proxy history (full year and peak to trough), measure its worst slide on record, and count simulated futures that miss the goal. |
| `cpb.fx` | The onshore local-currency slice is expected to give up the rate difference each year, which lowers the blended return, and loses the currency's drop times its share in a stress. |
| `cpb.proxies`, `cpb.calibrate` | Long-history month-end closes of one ETF per asset class, cached in the repo; the volatility table is recomputed from them. |
| `cpb.proposal` | One printable HTML page; the browser's print-to-PDF makes the PDF. |

## Quickstart

```bash
pip install -e ".[dev]"
pytest
python examples/bogota_family.py
```

The example builds the full proposal for a family based in Bogotá:
$5M, 60% offshore in Miami, 15-year horizon, goal "grow", tolerates a
15% loss in a bad year, COP exposure on the onshore 40%. Output lands
in `examples/output/bogota_family.html`.

## Data

`data/proxies.csv` (committed) holds Yahoo Finance month-end adjusted
closes for SPY, EFA, EEM, AGG, SHY, BIL, HYG and GLD since 1993; the
replays, the volatility table and the worst-slide line all read it, so
nothing needs the network. Refresh with `pip install -e ".[data]"` and
`python -m cpb.proxies`, then paste `python -m cpb.calibrate` into
`allocation.MODEL_VOLATILITY`. SOURCES.md says where every number comes
from. Bloomberg daily closes for 43 ETFs can also live in `data/` (not
committed); `cpb.data.load_closes` reads a wide CSV path and the example
reports a daily drawdown when the file is present.
