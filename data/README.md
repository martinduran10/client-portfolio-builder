# Data

Bloomberg daily closes for 43 ETFs. Not committed; the loader
(`cpb.data.load_closes`) reads a CSV path.

Expected format (`closes.csv`): a wide CSV with dates in the first
column and one column of daily closing prices per ticker.

```csv
date,IVV,IEFA,IEMG,AGG,SHY,BIL,...
2015-01-02,182.34,55.12,47.90,108.45,84.61,45.73,...
2015-01-05,179.08,54.30,46.88,108.90,84.70,45.73,...
```
