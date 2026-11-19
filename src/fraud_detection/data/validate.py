"""Data quality checks = test cases for data.

Each check returns Issues instead of raising, so you can REPORT everything
on raw data and FAIL on clean data with the same code.
"""

from dataclasses import dataclass

import pandas as pd

from fraud_detection.data import schema


@dataclass(frozen=True)
class Issue:
    dimension: str  # completeness / validity / uniqueness
    check: str
    column: str
    failing_rows: int
    severity: str = "error"  # "error" blocks the pipeline, "warning" is only reported

    def __str__(self) -> str:
        return (
            f"{self.severity.upper()} [{self.dimension}] {self.check} "
            f"on '{self.column}': {self.failing_rows} rows"
        )


class DataValidationError(Exception):
    def __init__(self, issues: list[Issue]):
        self.issues = issues
        details = "\n  ".join(str(i) for i in issues)
        super().__init__(f"{len(issues)} data quality check(s) failed:\n  {details}")


def check_required_columns(df: pd.DataFrame) -> list[Issue]:
    missing = [c for c in schema.REQUIRED_COLUMNS if c not in df.columns]
    return [Issue("completeness", "required column missing", c, len(df)) for c in missing]


def check_unique_id(df: pd.DataFrame) -> list[Issue]:
    dupes = int(df[schema.ID_COLUMN].duplicated(keep=False).sum())
    return [Issue("uniqueness", "duplicate id", schema.ID_COLUMN, dupes)] if dupes else []


def check_dtypes(df: pd.DataFrame) -> list[Issue]:
    issues = [
        Issue("validity", f"dtype is {df[c].dtype}, expected numeric", c, len(df))
        for c in [*schema.NUMERIC_COLUMNS, schema.TARGET_COLUMN]
        if not pd.api.types.is_numeric_dtype(df[c])
    ]
    ts = schema.TIMESTAMP_COLUMN
    if not pd.api.types.is_datetime64_any_dtype(df[ts]):
        issues.append(Issue("validity", f"dtype is {df[ts].dtype}, expected datetime", ts, len(df)))
    return issues


def check_ranges(df: pd.DataFrame) -> list[Issue]:
    issues = []
    for col, (low, high) in schema.VALUE_RANGES.items():
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue  # reported by check_dtypes
        bad = pd.Series(False, index=df.index)
        if low is not None:
            bad |= df[col] < low
        if high is not None:
            bad |= df[col] > high
        if bad.any():
            issues.append(Issue("validity", f"outside range [{low}, {high}]", col, int(bad.sum())))
    return issues


def check_allowed_values(df: pd.DataFrame) -> list[Issue]:
    issues = []
    for col, allowed in schema.ALLOWED_VALUES.items():
        bad = df[col].notna() & ~df[col].isin(allowed)
        if bad.any():
            issues.append(Issue("validity", "value not in allowed set", col, int(bad.sum())))
    return issues


def check_missing(df: pd.DataFrame, max_share: float) -> list[Issue]:
    share = df[schema.REQUIRED_COLUMNS].isna().mean()
    too_many = share[share > max_share]
    return [
        Issue(
            "completeness",
            f"missing share {share[c]:.1%} > {max_share:.0%}",
            c,
            int(df[c].isna().sum()),
        )
        for c in too_many.index
    ]


def run_checks(
    df: pd.DataFrame, max_missing_share: float = schema.MAX_MISSING_SHARE_CLEAN
) -> list[Issue]:
    issues = check_required_columns(df)
    if issues:
        return issues  # nothing else makes sense without the columns
    return [
        *check_unique_id(df),
        *check_dtypes(df),
        *check_ranges(df),
        *check_allowed_values(df),
        *check_missing(df, max_missing_share),
    ]


def errors_only(issues: list[Issue]) -> list[Issue]:
    return [i for i in issues if i.severity == "error"]


def validate_or_raise(df: pd.DataFrame) -> None:
    errors = errors_only(run_checks(df))
    if errors:
        raise DataValidationError(errors)
