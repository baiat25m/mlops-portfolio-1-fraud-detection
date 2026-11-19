"""What GOOD data looks like for the fraud dataset.

Dataset: "Credit Card Transactions Fraud Detection Dataset" (Kaggle, kartik2112).
Two files: fraudTrain.csv (Jan 2019 - Jun 2020) and fraudTest.csv (Jun 2020 - Dec 2020).
One row = one card transaction. Start with fraudTrain.csv.

Every rule the pipeline enforces lives here. Change the data contract here, nowhere else.
"""

ID_COLUMN = "trans_num"  # unique transaction id
TARGET_COLUMN = "is_fraud"  # 1 = fraud, 0 = legitimate
TIMESTAMP_COLUMN = "trans_date_trans_time"

NUMERIC_COLUMNS = ["amt", "lat", "long", "city_pop", "merch_lat", "merch_long"]

CATEGORIES = {
    "entertainment",
    "food_dining",
    "gas_transport",
    "grocery_net",
    "grocery_pos",
    "health_fitness",
    "home",
    "kids_pets",
    "misc_net",
    "misc_pos",
    "personal_care",
    "shopping_net",
    "shopping_pos",
    "travel",
}

# Column -> set of allowed values (validity checks)
ALLOWED_VALUES: dict[str, set] = {
    "category": CATEGORIES,
    "gender": {"M", "F"},
    TARGET_COLUMN: {0, 1},
}

# Column -> (min, max) inclusive; None = no bound (validity checks)
VALUE_RANGES: dict[str, tuple[float | None, float | None]] = {
    "amt": (0.01, 50_000),
    "lat": (-90, 90),
    "long": (-180, 180),
    "merch_lat": (-90, 90),
    "merch_long": (-180, 180),
    "city_pop": (1, None),
}

# The CSV starts with an unnamed row-number column. It's not data.
DROP_COLUMNS = ["Unnamed: 0"]

REQUIRED_COLUMNS = [
    ID_COLUMN,
    TARGET_COLUMN,
    TIMESTAMP_COLUMN,
    "merchant",
    "category",
    "gender",
    *NUMERIC_COLUMNS,
]

# Max share of missing values allowed AFTER cleaning (completeness checks)
MAX_MISSING_SHARE_CLEAN = 0.0

# Cleaning may drop at most this share of rows; more means something upstream broke
MAX_ROWS_DROPPED_SHARE = 0.05

# Share of fraud rows allowed; outside this range the labels are probably broken
FRAUD_RATE_RANGE = (0.001, 0.05)
