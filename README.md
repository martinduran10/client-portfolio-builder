# client-portfolio-builder

A client portfolio construction tool for a private wealth analyst.
Starts from a client profile, not a market signal. Every method is
explainable to a banker in one sentence — no optimizers, no
Black-Litterman, no machine learning, no factor models.

## How it works

| Module | One sentence |
|---|---|
| `cpb.profile` | The risk level 1-5 is the most conservative of what the client's loss tolerance, horizon, and goal each allow. |
| `cpb.allocation` | Each level owns a fixed mix; the 10-year return is a weighted average of per-asset estimates, shaved a tenth of any valuation premium per year (capped at ±2%). |
| `cpb.implementation` | One liquid ETF per asset class; dollars are weight times portfolio value. |
| `cpb.stress` | Replay 2008/2020/2022 on the mix, measure the worst historical slide, and count simulated futures that miss the goal. |
| `cpb.fx` | The onshore local-currency slice loses the currency's drop times its share, and is expected to drift by the rate difference. |
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

Bloomberg daily closes for 43 ETFs live in `data/` (not committed);
`cpb.data.load_closes` reads a wide CSV path. Everything except the
historical max-drawdown runs without it.
