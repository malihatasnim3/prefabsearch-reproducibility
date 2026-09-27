"""Train final LightGBM with exactly one class-balancing mechanism."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    RESULTS_DIR,
    build_lightgbm,
    calculate_metrics,
    load_config,
    load_model_dataset,
    read_ids,
    save_joblib,
    select_ids,
    write_json,
)


def main() -> None:
    config = load_config()
    data = load_model_dataset()
    train = select_ids(data, read_ids("train_ids.csv"), "train_ids.csv")
    test = select_ids(data, read_ids("test_ids.csv"), "test_ids.csv")
    features = config["features"]["columns"]
    target = config["target"]["name"]
    settings = config["models"]["lightgbm"]
    model = build_lightgbm(config)
    model.fit(train[features], train[target].astype(int))
    probability = model.predict_proba(test[features])[:, 1]
    threshold = float(settings["threshold"])
    prediction = (probability >= threshold).astype(int)
    output_dir = RESULTS_DIR / "model_predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "site_id": test["site_id"], "proxy_label": test[target].astype(int),
        "lightgbm_probability": probability, "lightgbm_prediction": prediction,
    }).to_csv(output_dir / "gradient_boosting_predictions.csv", index=False)
    save_joblib(model, "gradient_boosting.joblib")
    metrics = calculate_metrics(test[target], probability, prediction)
    write_json(RESULTS_DIR / "gradient_boosting_metrics.json", {
        "model": settings["implementation"], "features": features,
        "train_rows": int(len(train)), "test_rows": int(len(test)), "threshold": threshold,
        "class_balancing": "class_weight='balanced' only; no fit-time sample_weight",
        "configuration": {key: settings[key] for key in ["n_estimators", "learning_rate", "num_leaves", "max_depth", "min_child_samples", "reg_lambda", "random_state"]},
        **metrics,
    })
    print(metrics)


if __name__ == "__main__":
    main()

