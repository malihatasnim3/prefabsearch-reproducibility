"""Clean soil codes, rebuild the proxy target, and create the main site-ID split."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    PROCESSED_DIR,
    RESULTS_DIR,
    SOURCE_DIR,
    SPLITS_DIR,
    apply_feature_imputation,
    clean_soil_frame,
    ensure_directories,
    fit_feature_imputation,
    load_config,
    proxy_labels,
    raw_ground_difficulty,
    soil_special_masks,
    write_json,
)


def stratified_ids(frame: pd.DataFrame, config: dict) -> tuple[pd.Series, pd.Series]:
    settings = config["splits"]
    train_ids, test_ids = train_test_split(
        frame["site_id"].astype("string"),
        test_size=float(settings["test_size"]),
        random_state=int(settings["random_state"]),
        stratify=frame[config["target"]["name"]],
    )
    return train_ids.reset_index(drop=True), test_ids.reset_index(drop=True)


def make_split_stable(frame: pd.DataFrame, config: dict) -> tuple[pd.DataFrame, pd.Series, pd.Series, dict[str, float], int]:
    work = frame.copy()
    initial_median = float(work["ground_difficulty_score_raw"].median())
    work["ground_difficulty_score"] = work["ground_difficulty_score_raw"].fillna(initial_median)
    work["prefab_label"] = proxy_labels(work, config)

    for iteration in range(1, 11):
        train_ids, test_ids = stratified_ids(work, config)
        train = work.loc[work["site_id"].astype("string").isin(set(train_ids))]
        imputation = fit_feature_imputation(train, config)
        updated = work.copy()
        updated["ground_difficulty_score"] = updated["ground_difficulty_score_raw"].fillna(
            imputation["ground_difficulty_score"]
        )
        updated_labels = proxy_labels(updated, config)
        if updated_labels.equals(work["prefab_label"]):
            updated["prefab_label"] = updated_labels
            return updated, train_ids, test_ids, imputation, iteration
        work = updated
        work["prefab_label"] = updated_labels
    raise RuntimeError("Development-only ground-score imputation and stratified labels did not converge")


def main() -> None:
    ensure_directories()
    config = load_config()
    source_path = SOURCE_DIR / "analysis_grid_with_raw_lsc_codes.csv"
    source = pd.read_csv(source_path, dtype={"site_id": "string"})
    soil_columns = config["features"]["soil_columns"]
    if source["site_id"].isna().any() or source["site_id"].duplicated().any():
        raise ValueError("Source site IDs must be complete and unique")

    code98, water = soil_special_masks(source, soil_columns)
    cleaned = clean_soil_frame(source.loc[~water].copy(), soil_columns)
    for column in ["slope", "road_distance_m"]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned = cleaned.loc[
        cleaned["slope"].notna()
        & cleaned["road_distance_m"].notna()
        & cleaned["slope"].ge(0)
        & cleaned["road_distance_m"].ge(0)
    ].copy()
    cleaned["ground_difficulty_score_raw"] = raw_ground_difficulty(cleaned, config)
    cleaned["soil_valid_component_count"] = cleaned[soil_columns].notna().sum(axis=1).astype(int)
    cleaned["soil_missing"] = cleaned["soil_valid_component_count"].eq(0).astype(int)
    cleaned["complete_case_soil"] = cleaned[soil_columns].apply(
        lambda column: column.between(1.0, 8.0)
    ).all(axis=1).astype(int)
    cleaned["special_code_98"] = source.loc[~water, soil_columns].apply(
        pd.to_numeric, errors="coerce"
    ).eq(98.0).any(axis=1).astype(int).to_numpy()

    final, train_ids, test_ids, imputation, iterations = make_split_stable(cleaned, config)
    final["ground_score_imputed"] = final["ground_difficulty_score_raw"].isna().astype(int)
    final["prefab_label"] = proxy_labels(final, config)

    final_columns = [
        "site_id", "geometry", "slope", "road_distance_m", *soil_columns,
        "soil_valid_component_count", "soil_missing", "complete_case_soil",
        "special_code_98", "ground_difficulty_score_raw", "ground_score_imputed",
        "ground_difficulty_score", "prefab_label",
    ]
    final[final_columns].to_csv(PROCESSED_DIR / "site_features.csv", index=False)
    pd.DataFrame({"site_id": train_ids}).to_csv(SPLITS_DIR / "train_ids.csv", index=False)
    pd.DataFrame({"site_id": test_ids}).to_csv(SPLITS_DIR / "test_ids.csv", index=False)

    if set(train_ids) & set(test_ids):
        raise AssertionError("Main train/test IDs overlap")
    if set(train_ids) | set(test_ids) != set(final["site_id"]):
        raise AssertionError("Main split is not an exact partition of the final dataset")

    retained_source = source.loc[~water].copy()
    old_labels = retained_source.set_index("site_id")["legacy_prefab_label"].astype(int)
    new_labels = final.set_index("site_id")["prefab_label"].astype(int)
    changed_common = int((old_labels.loc[new_labels.index] != new_labels).sum())
    final_code98 = int(final["special_code_98"].sum())
    final_missing = int(final["soil_missing"].sum())
    final_complete = int(final["complete_case_soil"].sum())

    audit_rows = source.loc[code98 | water, [
        "site_id", *soil_columns, "legacy_ground_difficulty_score", "legacy_prefab_label"
    ]].copy()
    audit_rows["disposition"] = np.where(water.loc[audit_rows.index], "excluded_water", "retained_code_98_as_missing")
    audit_rows = audit_rows.merge(
        final[["site_id", "ground_difficulty_score", "prefab_label"]],
        on="site_id", how="left", validate="one_to_one"
    )
    audit_rows.to_csv(RESULTS_DIR / "soil_code_affected_sites.csv", index=False)

    before = {
        "candidate_observations": int(config["study"]["original_candidate_points"]),
        "invalid_elevation_exclusions": int(config["study"]["removed_without_dem_coverage"]),
        "other_feature_quality_exclusions": int(config["study"]["other_feature_quality_exclusions_before_soil_correction"]),
        "final_observations": int(len(source)),
        "water_excluded_observations": 0,
        "special_code_98_rows": int(code98.sum()),
        "special_code_99_rows": int(water.sum()),
        "complete_valid_soil_rows": int(source[soil_columns].apply(lambda c: pd.to_numeric(c, errors="coerce").between(1, 8)).all(axis=1).sum()),
        "fully_missing_valid_soil_rows": int(clean_soil_frame(source, soil_columns)[soil_columns].isna().all(axis=1).sum()),
        "proxy_positive_rows": int(source["legacy_prefab_label"].astype(int).sum()),
        "proxy_negative_rows": int(len(source) - source["legacy_prefab_label"].astype(int).sum()),
    }
    after = {
        "candidate_observations": int(config["study"]["original_candidate_points"]),
        "invalid_elevation_exclusions": int(config["study"]["removed_without_dem_coverage"]),
        "other_feature_quality_exclusions": int(config["study"]["other_feature_quality_exclusions_before_soil_correction"]),
        "final_observations": int(len(final)),
        "water_excluded_observations": int(water.sum()),
        "special_code_98_rows": final_code98,
        "special_code_99_rows": 0,
        "complete_valid_soil_rows": final_complete,
        "fully_missing_valid_soil_rows": final_missing,
        "proxy_positive_rows": int(final["prefab_label"].sum()),
        "proxy_negative_rows": int(len(final) - final["prefab_label"].sum()),
    }
    reasons = {
        "candidate_observations": "Unchanged upstream 100 m candidate grid.",
        "invalid_elevation_exclusions": "Unchanged upstream DEM-validity filter.",
        "other_feature_quality_exclusions": "Unchanged missing slope/road feature filter.",
        "final_observations": "Rows mapped as Water were excluded.",
        "water_excluded_observations": "Any of the six relevant LSC fields equal to 99 identifies Water.",
        "special_code_98_rows": "Code 98 rows are retained but treated as missing evidence.",
        "special_code_99_rows": "Code 99 rows are excluded from construction-screening candidates.",
        "complete_valid_soil_rows": "All six LSC values must be ordinary classes 1–8.",
        "fully_missing_valid_soil_rows": "Code 98 and other invalid values do not count as evidence.",
        "proxy_positive_rows": "Target rebuilt after corrected development-derived ground-score imputation.",
        "proxy_negative_rows": "Target rebuilt after corrected development-derived ground-score imputation.",
    }
    report = pd.DataFrame([
        {"metric": metric, "before": before[metric], "after": after[metric],
         "difference": after[metric] - before[metric], "reason": reasons[metric]}
        for metric in before
    ])
    report.to_csv(RESULTS_DIR / "final_dataset_change_report.csv", index=False)

    split_summary = {
        "procedure": "sklearn train_test_split by site_id",
        "test_size": float(config["splits"]["test_size"]),
        "random_state": int(config["splits"]["random_state"]),
        "stratify": "prefab_label",
        "fixed_point_iterations": iterations,
        "ground_score_imputation_reference": "valid development rows only",
        "rows": int(len(final)),
        "train_rows": int(len(train_ids)),
        "test_rows": int(len(test_ids)),
        "class_counts": {str(k): int(v) for k, v in final["prefab_label"].value_counts().sort_index().items()},
        "train_class_counts": {str(k): int(v) for k, v in final.set_index("site_id").loc[list(train_ids), "prefab_label"].value_counts().sort_index().items()},
        "test_class_counts": {str(k): int(v) for k, v in final.set_index("site_id").loc[list(test_ids), "prefab_label"].value_counts().sort_index().items()},
        "development_ground_difficulty_median": imputation["ground_difficulty_score"],
        "labels_changed_among_retained_sites": changed_common,
        "water_rows_removed": int(water.sum()),
    }
    write_json(RESULTS_DIR / "main_split_summary.json", split_summary)

    summary = {
        "original_candidate_points": before["candidate_observations"],
        "invalid_elevation_exclusions": before["invalid_elevation_exclusions"],
        "other_feature_quality_exclusions": before["other_feature_quality_exclusions"],
        "excluded_water_rows": after["water_excluded_observations"],
        "final_observations": after["final_observations"],
        "special_code_98_rows": after["special_code_98_rows"],
        "special_code_99_rows_in_final_dataset": 0,
        "final_soil_missing_rows": final_missing,
        "final_valid_soil_rows": int(len(final) - final_missing),
        "final_complete_case_rows": final_complete,
        "pre_cleanup_ground_score_imputations": 18085,
        "final_ground_score_imputations": int(final["ground_score_imputed"].sum()),
        "development_ground_difficulty_median": imputation["ground_difficulty_score"],
        "proxy_class_counts": split_summary["class_counts"],
        "proxy_prevalence": float(final["prefab_label"].mean()),
        "labels_changed_among_retained_sites": changed_common,
        "target_interpretation": config["target"]["interpretation"],
    }
    write_json(PROCESSED_DIR / "site_features_summary.json", summary)

    soil_report = f"""# Soil Code Correction Report

## Error corrected

The previous implementation clipped every numeric LSC value to 1–8. It therefore converted codes 98 and 99 to class 8 before calculating `ground_difficulty_score`.

## Final policy

- Ordinary values 1–8 remain ordinal limitation classes.
- Code 98 means Not assessed. It is converted to missing evidence before ground-score calculation, complete-case classification, and model-feature imputation.
- Code 99 means Water. A candidate is excluded when any of the six relevant mapped LSC fields equals 99. In the source table all six fields agree for each of the {int(water.sum())} affected rows, so this rule is unambiguous.
- Other out-of-domain values are treated as missing.

Partially observed records use the documented component weights renormalised over available valid components. Rows with no valid soil evidence use a ground-score median fitted on valid development observations only.

## Effect

- Code-98 rows retained as missing evidence: {final_code98}
- Code-99 Water rows excluded: {int(water.sum())}
- Final soil-missing rows: {final_missing}
- Final complete-case rows: {final_complete}
- Labels changed among retained sites: {changed_common}
- Final observations: {len(final)}
- Final proxy positives: {int(final['prefab_label'].sum())}
- Final proxy negatives: {int(len(final) - final['prefab_label'].sum())}

The full before/after counts are in `final_dataset_change_report.csv`; site-level effects for codes 98 and 99 are in `soil_code_affected_sites.csv`.
"""
    (RESULTS_DIR / "SOIL_CODE_CORRECTION_REPORT.md").write_text(soil_report, encoding="utf-8")
    print(json.dumps(split_summary, indent=2))


if __name__ == "__main__":
    main()

