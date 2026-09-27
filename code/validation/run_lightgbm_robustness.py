"""Run development-only CV, west-to-east sensitivity, and shuffled-label control."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    RESULTS_DIR,
    apply_feature_imputation,
    build_lightgbm,
    calculate_metrics,
    fit_feature_imputation,
    load_config,
    load_model_dataset,
    load_site_features,
    read_ids,
    select_ids,
    write_json,
)


def array_hash(values: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(values).tobytes()).hexdigest()


def main() -> None:
    config = load_config()
    data = load_model_dataset()
    features = config["features"]["columns"]
    target = config["target"]["name"]
    development = select_ids(data, read_ids("train_ids.csv"), "train_ids.csv")

    cv = StratifiedKFold(n_splits=int(config["robustness"]["cv_folds"]), shuffle=True, random_state=42)
    fold_predictions, fold_metrics = [], []
    for fold, (fit_index, validation_index) in enumerate(cv.split(development[features], development[target]), start=1):
        fit = development.iloc[fit_index]
        validation = development.iloc[validation_index]
        model = build_lightgbm(config, random_state=42)
        model.fit(fit[features], fit[target].astype(int))
        probability = model.predict_proba(validation[features])[:, 1]
        prediction = (probability >= 0.5).astype(int)
        values = calculate_metrics(validation[target], probability, prediction)
        fold_metrics.append({"fold": fold, **values})
        fold_predictions.append(pd.DataFrame({
            "site_id": validation["site_id"].to_numpy(), "fold": fold,
            "y_true": validation[target].to_numpy(), "probability": probability, "prediction": prediction,
        }))
    pd.concat(fold_predictions, ignore_index=True).to_csv(RESULTS_DIR / "lightgbm_cv_predictions.csv", index=False)
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"]
    cv_summary = {
        "design": "five-fold stratified CV within the main development set only",
        "development_rows": int(len(development)), "held_out_rows_in_cv": 0,
        "folds": fold_metrics,
        "summary": {metric: {"mean": float(np.mean([row[metric] for row in fold_metrics])),
                             "std": float(np.std([row[metric] for row in fold_metrics]))} for metric in metrics},
    }
    write_json(RESULTS_DIR / "lightgbm_cv_summary.json", cv_summary)

    site_features = load_site_features()
    spatial_ids = pd.read_csv(Path(__file__).resolve().parents[2] / "splits" / "spatial_split_ids.csv", dtype={"site_id": "string"})
    west_ids = spatial_ids.loc[spatial_ids["split"].eq("west_train"), "site_id"]
    east_ids = spatial_ids.loc[spatial_ids["split"].eq("east_test"), "site_id"]
    west_raw = select_ids(site_features, west_ids, "spatial west IDs")
    east_raw = select_ids(site_features, east_ids, "spatial east IDs")
    spatial_imputation = fit_feature_imputation(west_raw, config)
    west = apply_feature_imputation(west_raw, spatial_imputation, config)
    east = apply_feature_imputation(east_raw, spatial_imputation, config)
    spatial_model = build_lightgbm(config)
    spatial_model.fit(west[features], west[target].astype(int))
    spatial_probability = spatial_model.predict_proba(east[features])[:, 1]
    spatial_prediction = (spatial_probability >= 0.5).astype(int)
    spatial_metrics = calculate_metrics(east[target], spatial_probability, spatial_prediction)
    pd.DataFrame({
        "site_id": east["site_id"], "y_true": east[target].astype(int),
        "probability": spatial_probability, "prediction": spatial_prediction,
    }).to_csv(RESULTS_DIR / "spatial_validation_predictions.csv", index=False)
    write_json(RESULTS_DIR / "spatial_validation_results.json", {
        "interpretation": "directional internal sensitivity check, not external validation",
        "classification_threshold": 0.5, "class_balancing": "class_weight='balanced' only",
        "imputation_fit_scope": "west training rows only", "imputation_values": spatial_imputation,
        "west_train_rows": int(len(west)), "east_test_rows": int(len(east)), **spatial_metrics,
    })

    train = development
    test = select_ids(data, read_ids("test_ids.csv"), "test_ids.csv")
    full_labels = data[target].to_numpy(copy=True)
    rng = np.random.default_rng(int(config["robustness"]["shuffled_label_seed"]))
    shuffled_labels = rng.permutation(full_labels)
    shuffled_map = pd.Series(shuffled_labels, index=data["site_id"].astype("string"))
    shuffled_train_labels = train["site_id"].map(shuffled_map).astype(int)
    shuffled_test_labels = test["site_id"].map(shuffled_map).astype(int)
    shuffled_model = build_lightgbm(config)
    original_train_feature_hash = array_hash(train[features].to_numpy())
    shuffled_model.fit(train[features], shuffled_train_labels)
    shuffled_probability = shuffled_model.predict_proba(test[features])[:, 1]
    shuffled_prediction = (shuffled_probability >= 0.5).astype(int)
    shuffled_metrics = calculate_metrics(shuffled_test_labels, shuffled_probability, shuffled_prediction)
    pd.DataFrame({
        "site_id": test["site_id"], "y_true": shuffled_test_labels,
        "probability": shuffled_probability, "prediction": shuffled_prediction,
    }).to_csv(RESULTS_DIR / "shuffled_label_predictions.csv", index=False)
    write_json(RESULTS_DIR / "shuffled_label_results.json", {
        "seed": int(config["robustness"]["shuffled_label_seed"]),
        "feature_matrix_unchanged": True, "train_feature_matrix_sha256": original_train_feature_hash,
        "class_balancing": "class_weight='balanced' only", "classification_threshold": 0.5,
        **shuffled_metrics,
    })

    held = pd.read_csv(RESULTS_DIR / "held_out_metrics.csv").set_index("method").loc["gradient_boosting"]
    rows = [
        {"evaluation": "Random held-out", **{metric: held[metric] for metric in metrics}},
        {"evaluation": "Development five-fold CV (mean)", **{metric: cv_summary["summary"][metric]["mean"] for metric in metrics}},
        {"evaluation": "Development five-fold CV (std)", **{metric: cv_summary["summary"][metric]["std"] for metric in metrics}},
        {"evaluation": "West-to-east split", **{metric: spatial_metrics[metric] for metric in metrics}},
        {"evaluation": "Shuffled-label control", **{metric: shuffled_metrics[metric] for metric in metrics}},
    ]
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "gradient_boosting_robustness.csv", index=False)
    print(json.dumps({"cross_validation": cv_summary["summary"], "spatial": spatial_metrics, "shuffled": shuffled_metrics}, indent=2))


if __name__ == "__main__":
    main()

