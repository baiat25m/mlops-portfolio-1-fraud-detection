"""Turn raw data into clean data with ROW-LEVEL, deterministic fixes only.

Why no medians, means or outlier capping here?
Those use statistics of the whole dataset. Computing them before the
train/test split leaks test information into training. They belong in the
sklearn Pipeline later, fitted on the training set only.
"""

import logging
from dataclasses import dataclass, field

import pandas as pd

from fraud_detection.data import schema

logger = logging.getLogger(__name__)


@dataclass
class CleaningLog:
    """Every change is counted, so nothing is fixed silently."""

    steps: dict[str, int] = field(default_factory=dict)

    def record(self, step: str, affected: int) -> None:
        self.steps[step] = affected
        logger.info("clean: %-42s %d", step, affected)


def drop_export_columns(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    present = [c for c in schema.DROP_COLUMNS if c in df.columns]
    log.record("export artefact columns dropped", len(present))
    return df.drop(columns=present)


def strip_text(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    text_cols = df.select_dtypes(include=["str", "string"]).columns
    stripped = df.copy()
    changed = 0
    for col in text_cols:
        new = stripped[col].str.strip()
        changed += int(((new != stripped[col]) & stripped[col].notna()).sum())
        stripped[col] = new
    log.record("whitespace stripped (cells)", changed)
    return stripped


def coerce_types(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    result = df.copy()
    for col in [*schema.NUMERIC_COLUMNS, schema.TARGET_COLUMN]:
        before_missing = result[col].isna()
        result[col] = pd.to_numeric(result[col], errors="coerce")
        log.record(
            f"unparseable -> NaN in {col}", int((result[col].isna() & ~before_missing).sum())
        )

    ts = schema.TIMESTAMP_COLUMN
    before_missing = result[ts].isna()
    result[ts] = pd.to_datetime(result[ts], errors="coerce", format="%Y-%m-%d %H:%M:%S")
    log.record(f"unparseable -> NaT in {ts}", int((result[ts].isna() & ~before_missing).sum()))
    return result


def drop_incomplete_rows(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """A transaction without amount, time, label or merchant can't be used for training,
    and filling any of them in would be inventing data."""
    incomplete = df[schema.REQUIRED_COLUMNS].isna().any(axis=1)
    log.record("rows missing required values dropped", int(incomplete.sum()))
    return df[~incomplete]


def drop_exact_duplicates(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    deduped = df.drop_duplicates()
    log.record("exact duplicate rows dropped", len(df) - len(deduped))
    return deduped


def drop_conflicting_ids(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Same transaction id, different data: we can't know which row is true, so we
    quarantine (drop) all copies and report them rather than guess."""
    conflicted = df[schema.ID_COLUMN].duplicated(keep=False)
    if conflicted.any():
        ids = sorted(df.loc[conflicted, schema.ID_COLUMN].unique())
        logger.warning("Conflicting IDs quarantined: %s", ids[:10])
    log.record("rows with conflicting IDs dropped", int(conflicted.sum()))
    return df[~conflicted]


def drop_invalid_rows(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    invalid = pd.Series(False, index=df.index)
    for col, (low, high) in schema.VALUE_RANGES.items():
        if low is not None:
            invalid |= df[col] < low
        if high is not None:
            invalid |= df[col] > high
    for col, allowed in schema.ALLOWED_VALUES.items():
        invalid |= df[col].notna() & ~df[col].isin(allowed)
    log.record("rows breaking domain rules dropped", int(invalid.sum()))
    return df[~invalid]


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningLog]:
    log = CleaningLog()
    df = (
        raw.pipe(drop_export_columns, log)
        .pipe(strip_text, log)
        .pipe(coerce_types, log)
        .pipe(drop_incomplete_rows, log)
        .pipe(drop_exact_duplicates, log)
        .pipe(drop_conflicting_ids, log)
        .pipe(drop_invalid_rows, log)
        .astype({schema.TARGET_COLUMN: "int64"})
        .reset_index(drop=True)
    )
    log.record("rows in -> rows out (removed)", len(raw) - len(df))
    return df, log
