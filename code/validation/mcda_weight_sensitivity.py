"""Run 5,000 fixed-threshold ±20% MCDA weight perturbations."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import RESULTS_DIR, calculate_metrics, load_config, write_json


def summary(values: np.ndarray) -> dict[str, float]:
    return {"p05": float(np.quantile(values, 0.05)), "median": float(np.median(values)), "p95": float(np.quantile(values, 0.95))}


def main() -> None:
    config = load_config()
    components = pd.read_csv(RESULTS_DIR / "model_predictions" / "weighted_mcda_components.csv", dtype={"site_id": "string"})
    selection = json.loads((RESULTS_DIR / "mcda_threshold_selection.json").read_text(encoding="utf-8"))
    threshold = float(selection["selected_threshold"])
    weight_map = config["models"]["weighted_mcda"]["weights"]
    columns = list(weight_map)
    base_weights = np.asarray([weight_map[column] for column in columns], dtype=float)
    x = components[columns].to_numpy(dtype=float)
    y = components["proxy_label"].to_numpy(dtype=int)
    base_score = np.sum(x * base_weights, axis=1)
    base_prediction = (base_score >= threshold).astype(int)
    base_metrics = calculate_metrics(y, base_score, base_prediction)
    base_rank = pd.Series(base_score).rank(method="average")
    rng = np.random.default_rng(int(config["robustness"]["mcda_weight_seed"]))
    records = []
    runs = int(config["robustness"]["mcda_weight_scenarios"])
    fraction = float(config["robustness"]["mcda_weight_perturbation_fraction"])
    for _ in range(runs):
        weights = base_weights * rng.uniform(1.0 - fraction, 1.0 + fraction, len(base_weights))
        weights /= weights.sum()
        score = np.sum(x * weights, axis=1)
        prediction = (score >= threshold).astype(int)
        records.append({
            "rank_correlation_spearman": float(base_rank.corr(pd.Series(score).rank(method="average"))),
            "changed_classifications": int(np.count_nonzero(prediction != base_prediction)),
            "positive_predictions": int(prediction.sum()),
            "f1": float(f1_score(y, prediction, zero_division=0)),
        })
    frame = pd.DataFrame(records)
    result = {
        "design": {"runs": runs, "seed": int(config["robustness"]["mcda_weight_seed"]),
                   "perturbation": "each base weight multiplied independently by Uniform(0.8, 1.2), then renormalised",
                   "classification_threshold": threshold, "threshold_treatment": "held fixed",
                   "normalisation": "main development-fitted bounds"},
        "baseline": {"positive_predictions": int(base_prediction.sum()), **base_metrics},
        "summary": {column: summary(frame[column].to_numpy(dtype=float)) for column in frame.columns},
    }
    write_json(RESULTS_DIR / "mcda_weight_sensitivity.json", result)
    frame.to_csv(RESULTS_DIR / "mcda_weight_sensitivity_scenarios.csv", index=False)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

