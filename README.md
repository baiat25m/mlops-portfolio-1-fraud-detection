# mlops-portfolio-1-fraud-detection

Flags fraudulent credit card transactions. The project is built one step at a time, from
raw data to a tested, deployed and monitored ML service.

## Steps

| # | Step | State |
| --- | --- | --- |
| 1 | Data quality pipeline: load, check, clean, report | **in progress** |
| 2 | First model + evaluation | - |
| 3 | ... added one step at a time | |

## Step 1: data quality pipeline

```
raw CSV -> checks (report only) -> clean -> checks (block on ERROR)
        -> refuse if >5% of rows dropped -> clean.parquet + data_quality.md
```

### Run it

1. Download "Credit Card Transactions Fraud Detection Dataset" from Kaggle (kartik2112).
   Put `fraudTrain.csv` in `data/raw/`. (`data/` is in `.gitignore`: never commit data.)
2. Then:

```bash
uv sync
uv run pytest
uv run python -m fraud_detection.data.pipeline
```

Output: `data/processed/clean.parquet` and `reports/data_quality.md`.

### Your tasks for this step

- [ ] Read `schema.py`, then `clean.py`, then `validate.py`. Explain each function out loud.
- [ ] Run the pipeline on the real data. Read the report: explain every number in it.
- [ ] Add **one** check yourself, with a test: a fraud-rate sanity check. The dataset is about
      0.5% fraud. Make the pipeline fail if the fraud rate is below 0.1% or above 5%
      (that would mean the labels are broken). Put the limits in `schema.py`.
- [ ] Commit: `feat: data quality pipeline for fraud transactions`.
