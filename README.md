# Fraud detection: from raw data to a production ML service

Flags fraudulent credit card transactions. Built step by step into a tested, containerized,
monitored and automatically retrained ML service on Kubernetes and AWS.

**Status:** step 1 of the plan, the data quality pipeline. Progress by week is in
[STEPS.md](STEPS.md).

## Quick start

```bash
uv sync
uv run pytest
uv run python -m fraud_detection.data.pipeline
```

The pipeline needs the data first (see below). It writes `data/processed/clean.parquet`
and a report at `reports/data_quality.md`.

## Data

[Credit Card Transactions Fraud Detection Dataset](https://www.kaggle.com/datasets/kartik2112/fraud-detection)
(Kaggle). Synthetic, about 1.3 million transactions from Jan 2019 to Jun 2020, 0.58% fraud.

Download it and put `fraudTrain.csv` in `data/raw/`. Data is never committed (`/data/` is in
`.gitignore`). To read it from somewhere else, set `RAW_DATA_PATH`.

## How the pipeline works

```
raw CSV -> checks (report only) -> clean -> checks (block on any ERROR)
        -> stop if more than 5% of rows were dropped -> clean.parquet + report
```

| File | Job |
| --- | --- |
| `schema.py` | The data contract: columns, types, allowed values and ranges |
| `load.py` | Reads the raw CSV as it is |
| `clean.py` | Row-level fixes only, every change counted |
| `validate.py` | The checks; each returns issues instead of raising |
| `profiling.py` | Builds the data quality report |
| `pipeline.py` | Runs it all; config comes from environment variables |

## Project layout

```
src/fraud_detection/data/   pipeline code
tests/                      data quality tests (good data passes, broken data fails)
docs/decisions.md           why things are built the way they are
STEPS.md                    what gets built each week
```

## Development

```bash
uv run pre-commit install      # ruff runs on every commit
uv run ruff check . && uv run ruff format .
```
