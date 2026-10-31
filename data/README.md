# Data

## `proxies.csv` (committed)

Month-end adjusted closes (dividends reinvested) for the ETF proxies
behind each asset class, from Yahoo Finance via `yfinance`. The cache is
what tests, CI and the worked example read; nothing needs the network.

| Ticker | Stands for | First month-end |
|---|---|---|
| SPY | US equity (S&P 500) | 1993-01 |
| EFA | developed ex-US equity (MSCI EAFE) | 2001-08 |
| EEM | emerging-market equity (MSCI EM) | 2003-04 |
| AGG | US investment-grade bonds (Bloomberg US Aggregate) | 2003-09 |
| SHY | 1-3 year Treasuries | 2002-07 |
| BIL | 1-3 month T-bills (cash) | 2007-05 |
| HYG | US high-yield bonds (no model portfolio holds it yet) | 2007-04 |
| GLD | gold (no model portfolio holds it yet) | 2004-11 |

Refresh it with network access and the optional extra installed:

```bash
pip install -e ".[data]"
python -m cpb.proxies
```

The loader keeps each month's last daily close, drops a month still in
progress, and rounds to four decimals.

## `closes.csv` (not committed)

Bloomberg daily closes for 43 ETFs; the loader (`cpb.data.load_closes`)
reads a CSV path. A wide CSV with dates in the first column and one
column of daily closing prices per ticker:

```csv
date,IVV,IEFA,IEMG,AGG,SHY,BIL,...
2015-01-02,182.34,55.12,47.90,108.45,84.61,45.73,...
2015-01-05,179.08,54.30,46.88,108.90,84.70,45.73,...
```
