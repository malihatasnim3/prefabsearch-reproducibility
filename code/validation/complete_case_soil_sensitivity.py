"""Run the complete-case soil-coverage sensitivity analysis."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    RESULTS_DIR,
    build_lightgbm,
    build_mlp,
    calculate_metrics,
    fit_mcda_normalisation,
    load_config,
    load_site_features,
    mcda_components,
    mcda_scores,
    read_ids,
    select_f1_threshold,
    select_ids,
    write_json,
)


def main() -> None:
    config = load_config()
    source = load_site_features()
    soil = config["features"]["soil_columns"]
    complete = source.loc[source[soil].apply(lambda column: column.between(1, 8)).all(axis=1)].copy()
    train = select_ids(complete, read_ids("complete_case_train_ids.csv"), "complete_case_train_ids.csv")
    test = select_ids(complete, read_ids("complete_case_test_ids.csv"), "complete_case_test_ids.csv")
    features = config["features"]["columns"]
    target = config["target"]["name"]
    y_train, y_test = train[target].astype(int), test[target].astype(int)

    lightgbm = build_lightgbm(config)
    lightgbm.fit(train[features], y_train)
    lightgbm_probability = lightgbm.predict_proba(test[features])[:, 1]
    lightgbm_prediction = (lightgbm_probability >= 0.5).astype(int)

    scaler = StandardScaler()
    x_train = scaler.fit_transform(train[features])
    x_test = scaler.transform(test[features])
    mlp = build_mlp(config)
    mlp.fit(x_train, y_train)
    mlp_probability = mlp.predict_proba(x_test)[:, 1]
    mlp_prediction = (mlp_probability >= 0.5).astype(int)

    normalisation = fit_mcda_normalisation(train)
    development_score = mcda_scores(mcda_components(train, normalisation), config)
    mcda_threshold, threshold_record = select_f1_threshold(development_score, y_train)
    test_score = mcda_scores(mcda_components(test, normalisation), config)
    mcda_prediction = (test_score >= mcda_threshold).astype(int)

    evaluations = {
        "weighted_mcda": {"threshold": mcda_threshold, **calculate_metrics(y_test, test_score, mcda_prediction)},
        "lightgbm": {"threshold": 0.5, **calculate_metrics(y_test, lightgbm_probability, lightgbm_prediction)},
        "mlp": {"threshold": 0.5, "iterations": int(mlp.n_iter_), **calculate_metrics(y_test, mlp_probability, mlp_prediction)},
    }
    result = {
        "analysis_name": "complete-case soil-coverage sensitivity analysis",
        "interpretation": "internal sensitivity against the deterministic proxy label; not external validation",
        "definition": "all six LSC fields are ordinary values in 1-8",
        "source_rows": int(len(source)), "complete_case_rows": int(len(complete)),
        "positive_rows": int(complete[target].sum()), "positive_prevalence": float(complete[target].mean()),
        "split": {"random_state": int(config["splits"]["random_state"]), "stratified": True,
                  "train_rows": int(len(train)), "test_rows": int(len(test)),
                  "train_positive_rows": int(y_train.sum()), "test_positive_rows": int(y_test.sum())},
        "mcda_normalisation": normalisation, "mcda_threshold_selection": threshold_record,
        "evaluation": evaluations,
    }
    write_json(RESULTS_DIR / "complete_case_soil_results.json", result)
    rows = []
    for method, values in evaluations.items():
        tn, fp, fn, tp = np.asarray(values["confusion_matrix"]).ravel()
        rows.append({
            "method": method, "n_train": len(train), "n_test": len(test),
            "test_prevalence": float(y_test.mean()), "threshold": values["threshold"],
            **{key: values[key] for key in ["accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"]},
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        })
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "complete_case_soil_sensitivity.csv", index=False)
    pd.DataFrame({
        "site_id": test["site_id"], "y_true": y_test,
        "weighted_mcda_score": test_score, "weighted_mcda_prediction": mcda_prediction,
        "lightgbm_probability": lightgbm_probability, "lightgbm_prediction": lightgbm_prediction,
        "mlp_probability": mlp_probability, "mlp_prediction": mlp_prediction,
    }).to_csv(RESULTS_DIR / "complete_case_soil_predictions.csv", index=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

