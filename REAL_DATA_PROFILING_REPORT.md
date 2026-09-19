# Geomatrix Real Data Profiling Report

## 1) Source archive inspected

The attached archive was inspected from the Downloads directory and extracted under /tmp before any model training.

Archive:
- `GEOMATRIX_REAL_GOVT_DATA (2).zip`

Key files inside the archive:
- `GEOMATRIX_REAL_GOVT_DATA/README.md`
- `GEOMATRIX_REAL_GOVT_DATA/cleaned/geomatrix_project_master.csv`
- `GEOMATRIX_REAL_GOVT_DATA/cleaned/geomatrix_snapshots.csv`
- `GEOMATRIX_REAL_GOVT_DATA/cleaned/geomatrix_issues.csv`
- `GEOMATRIX_REAL_GOVT_DATA/cleaned/geomatrix_training.csv`
- `GEOMATRIX_REAL_GOVT_DATA/cleaned/geomatrix_highways_training.csv`
- `GEOMATRIX_REAL_GOVT_DATA/cleaned/geomatrix_railways_training.csv`
- `GEOMATRIX_REAL_GOVT_DATA/metadata/source_manifest.csv`
- `GEOMATRIX_REAL_GOVT_DATA/metadata/feature_dictionary.csv`

## 2) Data provenance and policy

The README states the following policy explicitly:
- all row-level facts come from official Government of India sources or deterministic derivations from those values
- no synthetic data, fabricated rows, random values, estimates, or imputed values were used
- missing information is left blank/NULL
- `delay_flag = 1` only when an official source documents a delay/stoppage or the official record shows a revised completion date later than the original
- `delay_flag = 0` requires demonstrable on-time completion, and the package says no retained record met that proof standard, so no zero labels were fabricated
- the model-training file excludes leakage fields and uses only official validation rules

This is a critical fact: the archive is intentionally designed to contain delayed cases only, not a balanced binary dataset.

## 3) Row counts and structure

Counts from the extracted files:
- `geomatrix_project_master.csv`: 127 rows
- `geomatrix_snapshots.csv`: 125 rows
- `geomatrix_issues.csv`: 35 rows
- `geomatrix_training.csv`: 83 rows
- `geomatrix_highways_training.csv`: 45 rows
- `geomatrix_railways_training.csv`: 38 rows

The clean training tables have the following columns:
- `project_id`
- `snapshot_date`
- `sector`
- `project_type`
- `implementing_agency`
- `ministry`
- `state`
- `district`
- `nh_number`
- `length_km`
- `project_cost_cr`
- `original_cost_cr`
- `expenditure_cr`
- `physical_progress_pct`
- `land_required_ha`
- `land_acquired_ha`
- `balance_land_ha`
- `possession_ha`
- `land_acquired_pct`
- `land_balance_pct`
- `expenditure_ratio`
- `days_to_original_deadline`
- `project_scale_category`
- `current_acquisition_stage`
- `known_issue_flags`
- `join_confidence`
- `delay_flag`
- `land_acquisition_delay_flag`
- `source_name`
- `source_url`
- `source_page`

## 4) Target distribution

The actual target field in the cleaned training tables is `delay_flag`.

Observed values:
- `geomatrix_training.csv`: 83 rows, `delay_flag` = 1 for all 83 rows
- `geomatrix_highways_training.csv`: 45 rows, `delay_flag` = 1 for all 45 rows
- `geomatrix_railways_training.csv`: 38 rows, `delay_flag` = 1 for all 38 rows

This is direct evidence that the dataset contains only positive class observations.

The `land_acquisition_delay_flag` field is also present, but it is not the main target for training and is only a subset indicator:
- `geomatrix_training.csv`: 28 rows flagged as 1.0, 55 missing/blank
- `geomatrix_railways_training.csv`: 28 rows flagged as 1.0, 10 missing/blank

## 5) Decision outcome

The real archive does not provide a valid binary classification dataset with both labels.

Therefore:
- training a classifier on this dataset would be statistically misleading
- synthetic class balancing or fabricated negatives would violate the project requirement and the archive policy
- the honest status is: model not trained — insufficient real labeled data

This matches the project’s existing guardrail in the ML code and the runtime message already used across the app.

## 6) Verified programmatic status

I verified the project behavior with:
- `pytest -q` from the project root

Result: `6 passed`.

This confirms the backend does not claim a trained model in the absence of a valid real target distribution.

## 7) Recommended next step

If the requirement is to have a trained predictive model, the next valid step is to acquire a second real dataset with verified `delay_flag = 0` examples from official sources and then retrain with those records only. Without real negative labels, no honest supervised model should be trained.
