"""raw CSV -> profile -> validate (report) -> clean -> validate (fail) -> parquet + report

    uv run python -m fraud_detection.data.pipeline

Config comes from environment variables (Week 1 habit):
    RAW_DATA_PATH      default data/raw/fraudTrain.csv
    CLEAN_DATA_PATH    default data/processed/clean.parquet
    REPORT_PATH        default reports/data_quality.md
    LOG_LEVEL          default INFO
"""

import logging
import os
import sys
from pathlib import Path

from fraud_detection.data import schema
from fraud_detection.data.clean import clean
from fraud_detection.data.load import load_raw
from fraud_detection.data.profiling import profile, write_report
from fraud_detection.data.validate import (
    DataValidationError,
    Issue,
    errors_only,
    run_checks,
)

logger = logging.getLogger("fraud_detection.data.pipeline")


def run(raw_path: Path, clean_path: Path, report_path: Path) -> None:
    raw = load_raw(raw_path)
    raw_issues = run_checks(raw, max_missing_share=1.0)
    for issue in raw_issues:
        logger.warning("raw data: %s", issue)

    cleaned, log = clean(raw)
    clean_issues = run_checks(cleaned)

    dropped = len(raw) - len(cleaned)
    if dropped > schema.MAX_ROWS_DROPPED_SHARE * len(raw):
        clean_issues.append(
            Issue(
                "completeness",
                f"cleaning dropped {dropped / len(raw):.1%} of rows "
                f"(limit {schema.MAX_ROWS_DROPPED_SHARE:.0%})",
                "*",
                dropped,
            )
        )

    write_report(report_path, profile(raw), profile(cleaned), raw_issues, clean_issues, log)
    logger.info("Report written to %s", report_path)

    for warning in [i for i in clean_issues if i.severity == "warning"]:
        logger.warning("clean data: %s", warning)
    errors = errors_only(clean_issues)
    if errors:  # never save data that fails the blocking checks
        raise DataValidationError(errors)
    clean_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_parquet(clean_path, index=False)
    logger.info("Clean data: %s rows -> %s", len(cleaned), clean_path)


def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    try:
        run(
            raw_path=Path(os.getenv("RAW_DATA_PATH", "data/raw/fraudTrain.csv")),
            clean_path=Path(os.getenv("CLEAN_DATA_PATH", "data/processed/clean.parquet")),
            report_path=Path(os.getenv("REPORT_PATH", "reports/data_quality.md")),
        )
    except (FileNotFoundError, DataValidationError) as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
