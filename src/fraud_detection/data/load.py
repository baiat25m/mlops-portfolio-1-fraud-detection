"""Load the raw dataset exactly as it is. No fixing here: fixing is clean.py's job."""

import logging
from pathlib import Path

import pandas as pd

from fraud_detection.data import schema

logger = logging.getLogger(__name__)


def load_raw(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data not found at {path}. Download the dataset and set RAW_DATA_PATH."
        )

    # IDs are labels, not numbers: read as text so they're never used as a numeric feature.
    df = pd.read_csv(path, dtype={"cc_num": "string", schema.ID_COLUMN: "string"})
    logger.info("Loaded %s rows x %s columns from %s", len(df), df.shape[1], path)
    return df
