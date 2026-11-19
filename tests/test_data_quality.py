"""Data-quality tests: checks PASS on good data and FAIL on deliberately corrupted data.

Each corruption test is a negative test case for the data. Add one every time you
discover a new way the data can be wrong.
"""

import pandas as pd
import pytest

from fraud_detection.data import schema
from fraud_detection.data.clean import clean
from fraud_detection.data.pipeline import run
from fraud_detection.data.validate import DataValidationError, run_checks, validate_or_raise


def make_row(i: int, **overrides) -> dict:
    """One raw transaction, shaped like a row of fraudTrain.csv."""
    row = {
        "Unnamed: 0": i,
        "trans_date_trans_time": f"2019-01-{1 + i % 28:02d} 10:{i % 60:02d}:00",
        "cc_num": f"4000123412341{i:03d}",
        "merchant": f"fraud_Merchant {i % 5}",
        "category": ["grocery_pos", "gas_transport", "shopping_net"][i % 3],
        "amt": 10.0 + i,
        "first": "Jane",
        "last": "Doe",
        "gender": "F" if i % 2 else "M",
        "street": "1 Main St",
        "city": "Springfield",
        "state": "IL",
        "zip": 62701,
        "lat": 39.8,
        "long": -89.6,
        "city_pop": 116_000,
        "job": "Engineer",
        "dob": "1985-04-12",
        "trans_num": f"tx{i:05d}",
        "unix_time": 1_325_376_018 + i,
        "merch_lat": 40.1,
        "merch_long": -89.9,
        "is_fraud": 1 if i % 20 == 0 else 0,
    }
    row.update(overrides)
    return row


@pytest.fixture
def raw_good() -> pd.DataFrame:
    return pd.DataFrame([make_row(i) for i in range(40)])


@pytest.fixture
def clean_good(raw_good) -> pd.DataFrame:
    cleaned, _ = clean(raw_good)
    return cleaned


# --- positive cases ---------------------------------------------------------


def test_clean_good_data_passes_all_checks(clean_good):
    assert run_checks(clean_good) == []
    validate_or_raise(clean_good)  # must not raise


def test_cleaning_keeps_all_good_rows_and_fixes_types(raw_good, clean_good):
    assert len(clean_good) == len(raw_good)
    assert "Unnamed: 0" not in clean_good.columns
    assert pd.api.types.is_datetime64_any_dtype(clean_good[schema.TIMESTAMP_COLUMN])
    assert clean_good[schema.TARGET_COLUMN].dtype == "int64"


# --- cleaning fixes what it should ------------------------------------------


def test_whitespace_in_categories_is_stripped(raw_good):
    raw = raw_good.copy()
    raw.loc[0, "category"] = " grocery_pos "
    cleaned, _ = clean(raw)
    assert cleaned.loc[0, "category"] == "grocery_pos"


def test_unparseable_timestamp_row_is_dropped(raw_good):
    raw = pd.concat([raw_good, pd.DataFrame([make_row(99, trans_date_trans_time="not a date")])])
    cleaned, log = clean(raw)
    assert "tx00099" not in set(cleaned["trans_num"])
    assert log.steps["unparseable -> NaT in trans_date_trans_time"] == 1


def test_exact_duplicates_dropped_conflicts_quarantined(raw_good):
    conflict = make_row(5, amt=999.0)  # same trans_num as row 5, different amount
    raw = pd.concat([raw_good, raw_good.iloc[[3]], pd.DataFrame([conflict])], ignore_index=True)
    cleaned, log = clean(raw)
    assert log.steps["exact duplicate rows dropped"] == 1
    assert "tx00005" not in set(cleaned["trans_num"])
    assert cleaned["trans_num"].is_unique


# --- negative cases: corrupted data must FAIL -----------------------------------


@pytest.mark.parametrize(
    ("column", "bad_value", "expected_check"),
    [
        ("amt", -5.0, "outside range"),
        ("amt", 0.0, "outside range"),
        ("lat", 123.0, "outside range"),
        ("category", "crypto", "value not in allowed set"),
        ("is_fraud", 2, "value not in allowed set"),
        ("merchant", None, "missing share"),
    ],
)
def test_corrupted_clean_data_fails(clean_good, column, bad_value, expected_check):
    corrupted = clean_good.copy()
    corrupted.loc[0, column] = bad_value
    issues = run_checks(corrupted)
    assert any(expected_check in issue.check for issue in issues), issues
    with pytest.raises(DataValidationError):
        validate_or_raise(corrupted)


def test_duplicate_id_fails(clean_good):
    corrupted = pd.concat([clean_good, clean_good.iloc[[0]]], ignore_index=True)
    assert any(i.dimension == "uniqueness" for i in run_checks(corrupted))


def test_text_amount_fails(clean_good):
    corrupted = clean_good.assign(amt=clean_good["amt"].astype(str))
    assert any("expected numeric" in i.check for i in run_checks(corrupted))


def test_text_timestamp_fails(clean_good):
    ts = schema.TIMESTAMP_COLUMN
    corrupted = clean_good.assign(**{ts: clean_good[ts].astype(str)})
    assert any("expected datetime" in i.check for i in run_checks(corrupted))


def test_missing_required_column_fails(clean_good):
    issues = run_checks(clean_good.drop(columns=[schema.TARGET_COLUMN]))
    assert issues and issues[0].check == "required column missing"


# --- end to end -----------------------------------------------------------------


def test_pipeline_end_to_end(tmp_path, raw_good):
    raw_path = tmp_path / "raw.csv"
    pd.concat([raw_good, raw_good.iloc[[0]]]).to_csv(raw_path, index=False)

    run(raw_path, tmp_path / "clean.parquet", tmp_path / "report.md")

    saved = pd.read_parquet(tmp_path / "clean.parquet")
    assert len(saved) == 40
    assert "all checks passed" in (tmp_path / "report.md").read_text()


def test_pipeline_refuses_when_cleaning_drops_too_many_rows(tmp_path, raw_good):
    raw_path = tmp_path / "raw.csv"
    raw_good.assign(amt=-1.0).to_csv(raw_path, index=False)  # e.g. an upstream export bug

    with pytest.raises(DataValidationError, match="cleaning dropped"):
        run(raw_path, tmp_path / "clean.parquet", tmp_path / "report.md")

    assert not (tmp_path / "clean.parquet").exists()
    assert "cleaning dropped" in (tmp_path / "report.md").read_text()
