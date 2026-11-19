# Design decisions

Why things are the way they are. Newest first. Add one every time you choose between two
reasonable options; these become interview answers.

## 2026-11-02: Fraud detection on the Sparkov credit card dataset

**Decision:** use "Credit Card Transactions Fraud Detection Dataset" (Kaggle, kartik2112).
**Why:** real fraud data is never public. This one is synthetic but has readable columns
(merchant, category, amount, location) and 18 months of timestamps, so retraining and drift
can later use real time periods instead of simulated ones.

## 2026-11-02: Cleaning uses row-level rules only

**Decision:** `clean.py` never computes medians, means or outlier caps.
**Why:** those come from the whole dataset. Computing them before the train/test split leaks
test data into training. They belong in the model pipeline, fitted on training data only.

## 2026-11-02: Conflicting transaction IDs are quarantined, not resolved

**Decision:** rows sharing a `trans_num` but with different values are all dropped and logged.
**Why:** there's no way to know which copy is correct.

## 2026-11-02: Pipeline refuses if cleaning drops more than 5% of rows

**Decision:** `MAX_ROWS_DROPPED_SHARE = 0.05` in `schema.py`.
**Why:** a large drop means something upstream broke. Failing loudly beats "succeeding" on
a fraction of the data.
