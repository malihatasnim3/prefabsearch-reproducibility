# Soil Code Correction Report

## Error corrected

The previous implementation clipped every numeric LSC value to 1–8. It therefore converted codes 98 and 99 to class 8 before calculating `ground_difficulty_score`.

## Final policy

- Ordinary values 1–8 remain ordinal limitation classes.
- Code 98 means Not assessed. It is converted to missing evidence before ground-score calculation, complete-case classification, and model-feature imputation.
- Code 99 means Water. A candidate is excluded when any of the six relevant mapped LSC fields equals 99. In the source table all six fields agree for each of the 9 affected rows, so this rule is unambiguous.
- Other out-of-domain values are treated as missing.

Partially observed records use the documented component weights renormalised over available valid components. Rows with no valid soil evidence use a ground-score median fitted on valid development observations only.

## Effect

- Code-98 rows retained as missing evidence: 81
- Code-99 Water rows excluded: 9
- Final soil-missing rows: 18030
- Final complete-case rows: 3187
- Labels changed among retained sites: 16
- Final observations: 21217
- Final proxy positives: 2395
- Final proxy negatives: 18822

The full before/after counts are in `final_dataset_change_report.csv`; site-level effects for codes 98 and 99 are in `soil_code_affected_sites.csv`.
