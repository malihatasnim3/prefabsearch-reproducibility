# Data dictionary

Geometry strings use Well-Known Text in GDA2020 / MGA zone 56 (EPSG:7856), except `data/study_area_boundary.geojson`, which is EPSG:4326. Model-specific prediction files omit geometry and join to sites through unique `site_id` values.

## Source and processed fields

| Field | Meaning | Unit or coding |
|---|---|---|
| `site_id` | Stable analysis-point identifier | String; unique and non-missing |
| `geometry` | Analysis-point coordinate | WKT point, EPSG:7856 |
| `slope` | DEM-derived local slope | Degrees; non-negative |
| `road_distance_m` | Euclidean distance to the acquired categorised-road layer | Metres; non-negative; early-screening approximation, not routed travel distance |
| `LSC_MstLmt` | Moisture limitation | Raw source: ordinary classes 1-8 plus special codes; processed: 1-8 or missing |
| `LSC_WatrEr` | Water-erosion limitation | Raw source: ordinary classes 1-8 plus special codes; processed: 1-8 or missing |
| `LSC_Watlog` | Waterlogging limitation | Raw source: ordinary classes 1-8 plus special codes; processed: 1-8 or missing |
| `LSC_Mass_m` | Mass-movement limitation | Raw source: ordinary classes 1-8 plus special codes; processed: 1-8 or missing |
| `LSC_Sh_Rk` | Shallow-rock limitation | Raw source: ordinary classes 1-8 plus special codes; processed: 1-8 or missing |
| `LSC_StrD` | Structural-decline limitation | Raw source: ordinary classes 1-8 plus special codes; processed: 1-8 or missing |
| `LSCMstLmtN` | Provider descriptive label | Audit only; not a predictor |
| `LimitnHazN` | Provider descriptive limitation/hazard label | Audit only; not a predictor |
| `legacy_soil_missing` | Pre-correction indicator retained for change audit | 0 or 1; never a predictor |
| `legacy_ground_difficulty_score` | Pre-correction score in which special codes had been clipped | 0-1; audit only; never a predictor |
| `legacy_prefab_label` | Pre-correction proxy target | 0 or 1; audit only; never a predictor |
| `soil_valid_component_count` | Number of the six LSC predictors with ordinary values | Integer 0-6 |
| `soil_missing` | No valid ordinary LSC evidence across all six fields | 1 when count is 0; otherwise 0 |
| `complete_case_soil` | All six LSC fields contain ordinary values | 1 only when all six are in 1-8 |
| `special_code_98` | Site had code 98 in at least one raw LSC field | 0 or 1; site retained as missing evidence |
| `ground_difficulty_score_raw` | Weighted, available-component-renormalised LSC composite | 0-1; missing when no valid LSC component |
| `ground_score_imputed` | Raw ground score was missing and replaced | 0 or 1 |
| `ground_difficulty_score` | Final score after development-fitted median imputation | 0-1; higher means more limiting |
| `prefab_label` / `proxy_label` | Deterministic proxy target | 1 iff slope <10 degrees, road distance <1000 m and ground score <0.45; else 0 |

## NSW LSC special-code policy

- Valid modelling domain: ordinary numeric classes **1-8**.
- **98 = Not assessed**: convert to missing before composite calculation, completeness classification and feature imputation.
- **99 = Water**: never convert to class 8; exclude a site when any of the six relevant mapped LSC fields equals 99.
- Any other out-of-domain or invalid special value: treat as missing.
- Partially observed records: calculate `ground_difficulty_score_raw` using only valid components and renormalise their documented weights to sum to one.

## Prediction and validation fields

| Pattern or field | Meaning |
|---|---|
| `*_score`, `*_probability` | Continuous held-out method output |
| `*_prediction` | Binary output at the documented threshold |
| `fold` | Development-only stratified cross-validation fold number |
| `easting_m` | EPSG:7856 x coordinate used for the spatial split |
| `split` | `west_train` or `east_test` for the directional sensitivity analysis |
| `importance_mean`, `importance_std` | Mean and standard deviation of held-out F1 decrease under 20 permutations; predictive, not causal importance |

## Count terminology

- `pre_cleanup_ground_score_imputations`: rows imputed in the pre-correction upstream export (18,085).
- `final_soil_missing_rows`: retained corrected rows with no valid soil component (18,030).
- `final_valid_soil_rows`: retained rows with at least one valid soil component (3,187).
- `final_complete_case_rows`: retained rows with all six valid fields (3,187 in this dataset; conceptually distinct from valid-soil rows).
- `excluded_water_rows`: code-99 Water rows removed (9).
- `special_code_98_rows`: code-98 rows retained as missing evidence (81).
- `special_code_99_rows`: raw source rows containing 99 (9); none remain in the final dataset.
