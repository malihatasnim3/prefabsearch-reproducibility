"""Compute held-out permutation importance with F1 scoring and 20 repeats."""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.inspection import permutation_importance

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import MODEL_DIR, RESULTS_DIR, load_config, load_model_dataset, read_ids, select_ids


def main() -> None:
    config = load_config()
    data = load_model_dataset()
    test = select_ids(data, read_ids("test_ids.csv"), "test_ids.csv")
    features = config["features"]["columns"]
    target = config["target"]["name"]
    repeats = int(config["robustness"]["permutation_repeats"])
    seed = int(config["robustness"]["permutation_seed"])
    lightgbm = joblib.load(MODEL_DIR / "gradient_boosting.joblib")
    mlp = joblib.load(MODEL_DIR / "mlp.joblib")
    scaler = joblib.load(MODEL_DIR / "mlp_scaler.joblib")
    specifications = [
        ("LightGBM", lightgbm, test[features]),
        ("MLP", mlp, scaler.transform(test[features])),
    ]
    rows = []
    for name, model, values in specifications:
        result = permutation_importance(
            model, values, test[target].astype(int), scoring="f1", n_repeats=repeats,
            random_state=seed, n_jobs=1,
        )
        for feature, mean, std in zip(features, result.importances_mean, result.importances_std, strict=True):
            rows.append({"method": name, "feature": feature, "importance_mean": float(mean),
                         "importance_std": float(std), "scoring": "f1", "repeats": repeats})
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "permutation_importance.csv", index=False)
    print(f"Wrote {len(rows)} permutation-importance rows")


if __name__ == "__main__":
    main()
