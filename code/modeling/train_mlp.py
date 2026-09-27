"""Train the final MLP with development-only scaling and internal validation."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    RESULTS_DIR,
    build_mlp,
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
    settings = config["models"]["mlp"]
    scaler = StandardScaler()
    x_train = scaler.fit_transform(train[features])
    x_test = scaler.transform(test[features])
    model = build_mlp(config)
    model.fit(x_train, train[target].astype(int))
    probability = model.predict_proba(x_test)[:, 1]
    threshold = float(settings["threshold"])
    prediction = (probability >= threshold).astype(int)
    output_dir = RESULTS_DIR / "model_predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "site_id": test["site_id"], "proxy_label": test[target].astype(int),
        "mlp_probability": probability, "mlp_prediction": prediction,
    }).to_csv(output_dir / "mlp_predictions.csv", index=False)
    save_joblib(model, "mlp.joblib")
    save_joblib(scaler, "mlp_scaler.joblib")
    metrics = calculate_metrics(test[target], probability, prediction)
    write_json(RESULTS_DIR / "mlp_metrics.json", {
        "model": settings["implementation"], "features": features,
        "train_rows": int(len(train)), "test_rows": int(len(test)), "threshold": threshold,
        "scaler_fit_scope": "development rows only",
        "early_stopping_scope": "internal validation fraction sampled only from development rows",
        "iterations": int(model.n_iter_), "configuration": settings, **metrics,
    })
    print(metrics)


if __name__ == "__main__":
    main()

