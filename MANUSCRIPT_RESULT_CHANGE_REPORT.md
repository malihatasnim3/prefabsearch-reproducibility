# Manuscript result change report

This report compares the pre-correction manuscript in `publication/results_in_engineering/manuscript.tex` with the final rebuilt artifacts in this release. It was prepared before editing the publication files. Unrounded machine-readable artifacts are authoritative; manuscript values below use publication-appropriate rounding.

## Scientific cause of the correction

The former pipeline clipped every numeric NSW Land and Soil Capability value to 1-8. Consequently, code 98 (Not assessed) and code 99 (Water) both contributed numerically as class 8. The final pipeline converts 98 to missing evidence, excludes a site when any of the six relevant fields is 99, renormalises ground-score weights over valid components, creates the split reproducibly by `site_id`, fits imputation and MCDA normalisation on development rows only, and uses only `class_weight="balanced"` for LightGBM. Every result was then rebuilt.

## Dataset, target and split

| Scientific value | Old manuscript value | Final verified value | Difference | Cause | Source artifact | Manuscript section(s) |
|---|---:|---:|---:|---|---|---|
| Initial candidate points | 21,554 | 21,554 | 0 - **VERIFIED - NO CHANGE** | Upstream grid unchanged | `results/final_dataset_change_report.csv` | 4.3.3 |
| Invalid-elevation exclusions | 103 | 103 | 0 - **VERIFIED - NO CHANGE** | DEM-validity filter unchanged | `results/final_dataset_change_report.csv` | 4.3.3 |
| Other terrain/accessibility exclusions | 225 | 225 | 0 - **VERIFIED - NO CHANGE** | Upstream feature-quality filter unchanged | `results/final_dataset_change_report.csv` | 4.3.3 |
| Water exclusions | 0 | 9 | +9 | Code 99 now means Water and is excluded | `results/final_dataset_change_report.csv` | Abstract; 4.3.3-4.3.4 |
| Final observations | 21,226 | 21,217 | -9 | Nine Water sites removed | `data/processed/site_features_summary.json` | Abstract; 3.2.2; 3.3.5; 3.4.1; 4.2.2; 4.3.3-4.3.4; 4.5; 5.2; 6.1 |
| Code-98 rows | previously counted as class 8 | 81 retained as missing | Policy change | Code 98 is Not assessed | `results/SOIL_CODE_CORRECTION_REPORT.md` | 4.3.3; limitations |
| Code-99 rows | previously counted as class 8 | 9 raw; 0 retained | Policy change | Code 99 is Water | `results/SOIL_CODE_CORRECTION_REPORT.md` | 4.3.3; limitations |
| Pre-cleanup ground-score imputations | 18,085 | 18,085 | 0 - **VERIFIED - NO CHANGE** | Historical upstream ledger count retained and separately named | `data/processed/site_features_summary.json` | 4.3.3 |
| Final fully soil-missing rows | 17,949 | 18,030 | +81 | Code-98 rows now missing; nine Water rows excluded | `data/processed/site_features_summary.json` | Abstract; 4.3.3; 4.5; 5.3; 6.2 |
| Final soil-missing percentage | 84.56% | 84.979% | +0.419 percentage points | Correct special-code policy and denominator | `data/processed/site_features_summary.json` | Same locations as preceding row |
| Rows with any valid soil evidence | 3,277 (described as observed) | 3,187 | -90 | 81 code-98 rows no longer valid evidence; 9 Water rows excluded | `data/processed/site_features_summary.json` | 4.3.3; 5.3.1 |
| Strict six-field complete cases | 3,277 | 3,187 | -90 | All six fields must be ordinary classes 1-8 | `results/complete_case_split_summary.json` | Abstract; 4.3.3; 5.3.1 |
| Development-fitted ground median | 0.3214285714 | 0.3214285714 | 0 - **VERIFIED - NO CHANGE** | Fit scope corrected to development-only; resulting value happens to match | `results/imputation_values.json` | 4.3.3 |
| Proxy-negative rows | 18,847 | 18,822 | -25 | Water removal and rebuilt labels | `results/main_split_summary.json` | 3.3.5; 4.2.2; 4.3.4; 5.2 |
| Proxy-positive rows | 2,379 | 2,395 | +16 | Corrected ground evidence changes 16 retained labels | `results/main_split_summary.json` | Same locations |
| Positive prevalence | 11.21% | 11.288% | +0.078 percentage points | Corrected numerator and denominator | `results/main_split_summary.json` | Abstract; 3.3.5; 4.2.2; 4.3.4; 5.2 |
| Development rows | 16,980 | 16,973 | -7 | Reproducible stratified 80/20 split of corrected data | `splits/train_ids.csv` | Abstract; 3.3.5; 4.2.2; 4.3.4; 6.1 |
| Held-out rows | 4,246 | 4,244 | -2 | Reproducible stratified 80/20 split of corrected data | `splits/test_ids.csv` | Same locations and performance table caption |
| Held-out positives | 476 inferred previously | 479 | +3 | Corrected stratified split | `results/main_split_summary.json` | Abstract/test-set description |
| MCDA threshold | 0.873501009 | 0.8730511441 | -0.0004498649 | Development-only normalisation and executable F1 selection | `results/mcda_threshold_selection.json` | 3.3.2; 4.3.5; model-configuration table |
| Target thresholds | slope <10 degrees; distance <1000 m; ground <0.45 | same | 0 - **VERIFIED - NO CHANGE** | Research rule intentionally unchanged | `config/research_config.yaml` | Abstract; 4.2.2; 4.3.4 |

## Main held-out results

| Method/value | Old manuscript value | Final verified value | Difference | Cause | Source artifact | Manuscript section(s) |
|---|---:|---:|---:|---|---|---|
| MCDA accuracy | 0.9432 | 0.9423 | -0.0009 | Corrected data/split and development-only scaling/threshold | `results/weighted_mcda_metrics.json` | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| MCDA precision | 0.7990 | 0.7882 | -0.0108 | Same | same | 4.3.8; 5.2.1; Table 5.1 |
| MCDA recall | 0.6597 | 0.6681 | +0.0084 | Same | same | same |
| MCDA F1 | 0.7227 | 0.7232 | +0.0005 | Same | same | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| MCDA ROC-AUC | 0.9264 | 0.9275 | +0.0011 | Same | same | 4.3.8; 5.2.1; Table 5.1 |
| MCDA AP | 0.7958 | 0.7911 | -0.0047 | Same | same | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| LightGBM accuracy | 0.9979 | 0.9988 | +0.0009 | Corrected data/split and removal of duplicate balancing | `results/gradient_boosting_metrics.json` | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| LightGBM precision | 0.9875 | 0.9958 | +0.0083 | Same | same | 4.3.8; 5.2.1; Table 5.1 |
| LightGBM recall | 0.9937 | 0.9937 | approximately 0 - **VERIFIED - NO MATERIAL CHANGE** | Same | same | same |
| LightGBM F1 | 0.9906 | 0.9948 | +0.0042 | Same | same | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| LightGBM ROC-AUC | 0.99997 | 0.99998 | +0.00001 | Same | same | 4.3.8; 5.2.1; Table 5.1 |
| LightGBM AP | 0.9998 | 0.99987 | +0.00007 | Same | same | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| MLP accuracy | 0.9967 | 0.9958 | -0.0009 | Corrected data/split; development-fitted scaler retraining | `results/mlp_metrics.json` | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| MLP precision | 0.9853 | 0.9832 | -0.0021 | Same | same | 4.3.8; 5.2.1; Table 5.1 |
| MLP recall | 0.9853 | 0.9791 | -0.0062 | Same | same | same |
| MLP F1 | 0.9853 | 0.9812 | -0.0041 | Same | same | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| MLP ROC-AUC | 0.99986 | 0.99986 | rounded value unchanged - **VERIFIED - NO CHANGE** | Same | same | 4.3.8; 5.2.1; Table 5.1 |
| MLP AP | 0.9989 | 0.99896 | +0.00006 | Same | same | Abstract; 4.3.8; 5.2.1; Table 5.1; 6.1 |
| MCDA confusion matrix | [[3,688, 79], [162, 317]] | [[3,679, 86], [159, 320]] | errors 241 -> 245 | Corrected data/split/threshold | `results/verified_metrics.json` | 5.2.2; Figure 4 |
| LightGBM confusion matrix | [[3,761, 6], [3, 476]] | [[3,763, 2], [3, 476]] | errors 9 -> 5 | Corrected training and balancing | same | 5.2.2; Figure 4 |
| MLP confusion matrix | [[3,760, 7], [7, 472]] | [[3,757, 8], [10, 469]] | errors 14 -> 18 | Corrected data/split/retraining | same | 5.2.2; Figure 4 |
| All three agree | 3,998 | 3,987 | -11 | Corrected predictions | `results/verified_metrics.json` | 5.2.2 |
| MCDA vs LightGBM disagreements | 240 | 250 | +10 | Corrected predictions | same | 5.2.2 |
| MCDA vs MLP disagreements | 241 | 249 | +8 | Corrected predictions | same | 5.2.2 |
| LightGBM vs MLP disagreements | 15 | 15 | 0 - **VERIFIED - NO CHANGE** | Corrected predictions happen to retain the count | same | 5.2.2 |

The manuscript phrase "balanced sample weights" must be replaced by `class_weight="balanced"` only. The old implementation combined `class_weight` and fit-time sample weights; the final one uses exactly one balancing mechanism. The MLP iteration count changes from 148 to 113 after retraining (`results/mlp_metrics.json`).

## Boundary-window analysis

| Boundary band | Old manuscript | Final verified | Change/cause | Source | Manuscript section |
|---|---|---|---|---|---|
| Road +/-100 m | n=145; MCDA 61 errors; LightGBM 6; MLP 6 | n=150; MCDA 59; LightGBM 5; MLP 11 | Corrected held-out membership/predictions | `results/boundary_analysis.csv` | 5.3.1 |
| Slope +/-0.5 degrees | n=35; MCDA 10; LightGBM 3; MLP 5 | n=41; MCDA 8; LightGBM 0; MLP 1 | Same | same | 5.3.1 |
| Ground +/-0.025 | n=86; MCDA 17; LightGBM 0; MLP 0 | n=94; MCDA 13; LightGBM 0; MLP 0 | Same | same | 5.3.1 |
| Overlapping bands | n=12; MCDA 3; LightGBM 0; MLP 2 | n=9; MCDA 5; LightGBM 0; MLP 0 | Same | same | 5.3.1 |
| Outside bands | n=3,968; MCDA 150; LightGBM 0; MLP 1 | n=3,950; MCDA 160; LightGBM 0; MLP 6 | Same | same | 5.3.1 |

## Complete-case soil-coverage sensitivity

The cohort changes from 3,277 to 3,187 rows. The split changes from 2,621/656 to 2,549/638; final test positives remain 200, so prevalence changes from 30.49% to 31.35%.

| Method/value | Old manuscript | Final verified | Difference/cause | Source | Manuscript section |
|---|---:|---:|---|---|---|
| MCDA accuracy / precision / recall / F1 | 0.8887 / 0.8325 / 0.7950 / 0.8133 | 0.8746 / 0.8226 / 0.7650 / 0.7927 | Correct strict cohort and development-fitted MCDA | `results/complete_case_soil_results.json` | 5.3.1 and table |
| MCDA ROC-AUC / AP / confusion | 0.9332 / 0.8762 / [[424,32],[41,159]] | 0.9286 / 0.8777 / [[405,33],[47,153]] | Same | same | same |
| LightGBM accuracy / precision / recall / F1 | 0.9985 / 1.0000 / 0.9950 / 0.9975 | 0.9953 / 0.9852 / 1.0000 / 0.9926 | Correct strict cohort and single balancing | same | same |
| LightGBM ROC-AUC / AP / confusion | 0.9992 / 0.9986 / [[456,0],[1,199]] | 1.0000 / 1.0000 / [[435,3],[0,200]] | Same | same | same |
| MLP accuracy / precision / recall / F1 | 0.9909 / 0.9755 / 0.9950 / 0.9851 | 0.9953 / 0.9900 / 0.9950 / 0.9925 | Correct strict cohort and retraining | same | same |
| MLP ROC-AUC / AP / confusion | 0.9999 / 0.9997 / [[451,5],[1,199]] | 0.99989 / 0.99976 / [[436,2],[1,199]] | Same | same | same |

## Robustness results

| Scientific value | Old manuscript value | Final verified value | Difference/cause | Source artifact | Manuscript section |
|---|---|---|---|---|---|
| LightGBM development accuracy/F1 | 0.99994 / 0.99974 | 0.99965 / 0.99844 | Retrained corrected model, single balancing | Recomputed from `models/gradient_boosting.joblib` and development IDs | 5.3.3 |
| Development-only CV accuracy | 0.99859 +/- 0.00076 | 0.99894 +/- 0.00092 | Corrected development set and model policy | `results/lightgbm_cv_summary.json` | 5.3.3 |
| CV precision | 0.99166 +/- 0.00614 | 0.99532 +/- 0.00473 | Same | same | 5.3.3 |
| CV recall | 0.99580 +/- 0.00133 | 0.99530 +/- 0.00626 | Same | same | 5.3.3 |
| CV F1 | 0.99372 +/- 0.00336 | 0.99530 +/- 0.00411 | Same | same | Abstract; 5.3.3 |
| CV ROC-AUC | 0.99996 +/- 0.00003 | 0.99997 +/- 0.00003 | Same; rounded small change | same | 5.3.3 |
| CV AP | not reported in paragraph | 0.99976 +/- 0.00024 | Added conventional imbalance-aware metric | same | 5.3.3 |
| West/east counts | 10,640 / 10,586 | 10,639 / 10,578 | -1 / -8 after Water exclusion | `results/spatial_split_summary.json` | Abstract; 5.3.3 |
| West-to-east accuracy/precision/recall/F1 | 0.99830 / 0.98837 / 0.99765 / 0.99299 | 0.99811 / 0.98773 / 0.99690 / 0.99230 | Corrected split/model | `results/spatial_validation_results.json` | 5.3.3 |
| West-to-east ROC-AUC / AP | 0.99996 / not reported | 0.99995 / 0.99965 | Corrected split; AP added | same | 5.3.3 |
| West-to-east confusion | [[9293,15],[3,1275]] | [[9270,16],[4,1288]] | Corrected split/model | same | 5.3.3 |
| Shuffled-label F1 | 0.1415 | 0.1782 | +0.0367; labels reshuffled on corrected fixed features | `results/shuffled_label_results.json` | Abstract; 5.3.3 |
| Shuffled-label ROC-AUC | 0.5044 | 0.4929 | -0.0115 | Same | same | Abstract; 5.3.3 |
| Shuffled-label AP | not reported | 0.1179 | Added | same | 5.3.3 |

## MCDA preference sensitivity

| Outcome | Old manuscript | Final verified | Difference/cause | Source | Manuscript section |
|---|---|---|---|---|---|
| Spearman median (5th-95th) | 0.9985 (0.9918-0.9998) | 0.99836 (0.99110-0.99980) | Corrected held-out scores/threshold | `results/mcda_weight_sensitivity.json` | 5.3.3 and table |
| Changed classifications median (5th-95th) | 136 (25-333) | 132 (22-325) | Same | same | same |
| Positive predictions baseline; median (5th-95th) | 393; 392.5 (155-726) | 406; 404 (155-729.05) | Same | same | same |
| F1 baseline; median (5th-95th) | 0.7227; 0.6824 (0.4778-0.7521) | 0.7232; 0.6854 (0.4661-0.7511) | Same | same | same |

## Permutation importance

| Method/feature | Old manuscript mean +/- SD | Final verified mean +/- SD | Difference/cause | Source | Manuscript section |
|---|---:|---:|---|---|---|
| LightGBM road distance | 0.8490 +/- 0.0132 | 0.8520 +/- 0.0125 | Corrected model/test set | `results/permutation_importance.csv` | 5.3.2 |
| LightGBM slope | 0.1848 +/- 0.0075 | 0.1900 +/- 0.0055 | Same | same | 5.3.2 |
| LightGBM ground difficulty | 0.0183 +/- 0.0017 | 0.0108 +/- 0.0022 | Same | same | 5.3.2 |
| MLP road distance | 0.8408 +/- 0.0135 | 0.8349 +/- 0.0128 | Corrected model/test set | same | 5.3.2 |
| MLP slope | 0.1807 +/- 0.0071 | 0.1773 +/- 0.0062 | Same | same | 5.3.2 |
| MLP moisture limitation | 0.1035 +/- 0.0061 | 0.1314 +/- 0.0064 | Same | same | 5.3.2 |
| MLP ground difficulty | 0.0683 +/- 0.0037 | 0.1069 +/- 0.0058 | Same | same | 5.3.2 |

All other feature-level values remain machine-readable in `results/permutation_importance.csv`; the manuscript should continue describing these as predictive dependence under permutation, not causal importance.

## Values verified without scientific change

- Study area: 215.60 km2 and published approximate bounds - **VERIFIED - NO CHANGE**.
- Analysis grid spacing: 100 m - **VERIFIED - NO CHANGE**.
- Operational CRS: EPSG:7856 - **VERIFIED - NO CHANGE**.
- Nine predictors and all fixed MCDA weights - **VERIFIED - NO CHANGE**.
- Proxy thresholds - **VERIFIED - NO CHANGE**.
- LightGBM structural hyperparameters (300 estimators, learning rate 0.10, 15 leaves, minimum 20 child samples) - **VERIFIED - NO CHANGE**; balancing implementation changed.
- MLP architecture/hyperparameters and fixed 0.50 threshold - **VERIFIED - NO CHANGE**; fitted artifact/iteration count changed.

## Required manuscript edits

Update the abstract, methods, experiment setup/configuration tables, dataset ledger, soil terminology, all result paragraphs/tables, captions with sample sizes, conclusion, and every occurrence of the old missingness percentage. Replace the statement that codes 98 and 99 are both missing with the final distinction: 98 is missing/Not assessed and 99 is Water/excluded. Replace "balanced sample weights" with a single `class_weight="balanced"` policy. Replace all six publication figures with the corrected release figures while preserving journal framing and captions.

The journal highlights were also corrected: mapped sites changed from 21,226 to 21,217; rounded LightGBM F1 changed from 0.991 to 0.995; and rounded shuffled-label ROC-AUC changed from 0.504 to 0.493. The remaining two qualitative highlight statements were verified without change.
