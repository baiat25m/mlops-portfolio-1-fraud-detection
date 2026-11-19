"""Profile a DataFrame and write a human-readable data-quality report."""

from datetime import datetime
from pathlib import Path

import pandas as pd

from fraud_detection.data.clean import CleaningLog
from fraud_detection.data.validate import Issue


def profile(df: pd.DataFrame) -> dict:
    numeric = df.select_dtypes("number")
    q1, q3 = numeric.quantile(0.25), numeric.quantile(0.75)
    iqr = q3 - q1
    outliers = ((numeric < q1 - 1.5 * iqr) | (numeric > q3 + 1.5 * iqr)).sum()
    return {
        "rows": len(df),
        "columns": df.shape[1],
        "duplicate_rows": int(df.duplicated().sum()),
        "missing_by_column": df.isna().sum()[lambda s: s > 0].to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "numeric_summary": numeric.describe().round(2),
        "iqr_outliers": outliers[outliers > 0].to_dict(),
        "constant_columns": sorted(df.columns[df.nunique() == 1]),
    }


def _section(title: str, p: dict) -> str:
    missing = (
        "\n".join(f"| {c} | {n} |" for c, n in p["missing_by_column"].items()) or "| (none) | 0 |"
    )
    outliers = ", ".join(f"{c}: {n}" for c, n in p["iqr_outliers"].items()) or "none"
    dtypes = "\n".join(f"| {c} | {t} |" for c, t in p["dtypes"].items())
    return f"""## {title}

- Rows: {p["rows"]:,} | Columns: {p["columns"]} | Exact duplicate rows: {p["duplicate_rows"]}
- IQR outliers (flagged, not removed): {outliers}
- Constant columns: {", ".join(p["constant_columns"]) or "none"}

| Column | Missing |
| --- | --- |
{missing}

<details><summary>dtypes</summary>

| Column | dtype |
| --- | --- |
{dtypes}

</details>

```text
{p["numeric_summary"].to_string()}
```
"""


def write_report(
    path: Path,
    raw: dict,
    clean: dict,
    raw_issues: list[Issue],
    clean_issues: list[Issue],
    log: CleaningLog,
) -> None:
    raw_list = "\n".join(f"- {i}" for i in raw_issues) or "- none"
    clean_list = "\n".join(f"- {i}" for i in clean_issues) or "- none: all checks passed"
    steps = "\n".join(f"| {step} | {n} |" for step, n in log.steps.items())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""# Data quality report

Generated {datetime.now():%Y-%m-%d %H:%M}

## Checks on RAW data (expected to find problems)
{raw_list}

## Cleaning steps
| Step | Rows / cells affected |
| --- | --- |
{steps}

## Checks on CLEAN data (no ERROR allowed; read every WARNING)
{clean_list}

{_section("Raw profile", raw)}
{_section("Clean profile", clean)}
""",
        encoding="utf-8",
    )
