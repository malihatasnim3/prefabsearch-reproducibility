"""Recompute held-out metrics, disagreements, soil strata, and boundary windows."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import PROCESSED_DIR, RESULTS_DIR, calculate_metrics, load_config, write_json

METHODS = {
    "weighted_mcda": ("weighted_mcda_score", "weighted_mcda_prediction"),
    "gradient_boosting": ("lightgbm_probability", "lightgbm_prediction"),
    "mlp": ("mlp_probability", "mlp_prediction"),
}


def boundary_analysis(predictions: pd.DataFrame, config: dict) -> pd.DataFrame:
    features = pd.read_csv(
        PROCESSED_DIR / "site_features.csv",
        usecols=["site_id", "slope", "road_distance_m", "ground_difficulty_score"],
        dtype={"site_id": "string"},
    )
    work = predictions.merge(features, on="site_id", how="left", validate="one_to_one")
    windows = config["robustness"]["boundary_windows"]
    flags = pd.DataFrame({
        "slope": (work["slope"] - config["target"]["slope_threshold_deg"]).abs() <= windows["slope_degrees"],
        "road": (work["road_distance_m"] - config["target"]["road_distance_threshold_m"]).abs() <= windows["road_distance_m"],
        "ground": (work["ground_difficulty_score"] - config["target"]["ground_difficulty_threshold"]).abs() <= windows["ground_difficulty"],
    })
    count = flags.sum(axis=1)
    work["band"] = "outside_selected_boundary_bands"
    work.loc[count > 1, "band"] = "overlapping_boundary_bands"
    work.loc[(count == 1) & flags["slope"], "band"] = "slope_within_0.5_degrees"
    work.loc[(count == 1) & flags["road"], "band"] = "road_distance_within_100_m"
    work.loc[(count == 1) & flags["ground"], "band"] = "ground_score_within_0.025"
    rows = []
    for band, group in work.groupby("band", sort=True):
        rows.append({
            "band": band, "n": int(len(group)), "positive_prevalence": float(group["proxy_label"].mean()),
            "weighted_mcda_errors": int((group["weighted_mcda_prediction"] != group["proxy_label"]).sum()),
            "gradient_boosting_errors": int((group["lightgbm_prediction"] != group["proxy_label"]).sum()),
            "mlp_errors": int((group["mlp_prediction"] != group["proxy_label"]).sum()),
            "all_methods_agree": int(((group["weighted_mcda_prediction"] == group["lightgbm_prediction"]) & (group["weighted_mcda_prediction"] == group["mlp_prediction"])).sum()),
        })
    return pd.DataFrame(rows)


def main() -> None:
    config = load_config()
    predictions = pd.read_csv(RESULTS_DIR / "held_out_predictions.csv", dtype={"site_id": "string"})
    all_metrics = {}
    csv_rows = []
    for method, (score, prediction) in METHODS.items():
        values = calculate_metrics(predictions["proxy_label"], predictions[score], predictions[prediction])
        all_metrics[method] = values
        csv_rows.append({"method": method, **{key: value for key, value in values.items() if key != "confusion_matrix"}})
    pd.DataFrame(csv_rows).to_csv(RESULTS_DIR / "held_out_metrics.csv", index=False)
    disagreements = {
        "weighted_mcda_vs_gradient_boosting": int((predictions["weighted_mcda_prediction"] != predictions["lightgbm_prediction"]).sum()),
        "weighted_mcda_vs_mlp": int((predictions["weighted_mcda_prediction"] != predictions["mlp_prediction"]).sum()),
        "gradient_boosting_vs_mlp": int((predictions["lightgbm_prediction"] != predictions["mlp_prediction"]).sum()),
        "all_three_agree": int(((predictions["weighted_mcda_prediction"] == predictions["lightgbm_prediction"]) & (predictions["weighted_mcda_prediction"] == predictions["mlp_prediction"])).sum()),
    }
    features = pd.read_csv(PROCESSED_DIR / "site_features.csv", usecols=["site_id", "soil_missing"], dtype={"site_id": "string"})
    soil_work = predictions.merge(features, on="site_id", validate="one_to_one")
    strata = {}
    for method, (score, prediction) in METHODS.items():
        strata[method] = {}
        for flag, name in [(0, "valid_soil_evidence"), (1, "soil_missing")]:
            subset = soil_work.loc[soil_work["soil_missing"].eq(flag)]
            strata[method][name] = calculate_metrics(subset["proxy_label"], subset[score], subset[prediction])
    write_json(RESULTS_DIR / "verified_metrics.json", {
        "held_out": all_metrics, "held_out_disagreement": disagreements,
        "soil_coverage_sensitivity": strata,
        "interpretation": "agreement with a deterministic proxy target, not field validation",
    })
    boundary_analysis(predictions, config).to_csv(RESULTS_DIR / "boundary_analysis.csv", index=False)
    print(all_metrics)


if __name__ == "__main__":
    main()
