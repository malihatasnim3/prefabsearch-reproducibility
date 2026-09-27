"""Apply the development-fitted weighted MCDA to held-out sites."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    RESULTS_DIR,
    calculate_metrics,
    load_config,
    load_model_dataset,
    mcda_components,
    mcda_scores,
    read_ids,
    select_ids,
    write_json,
)


def main() -> None:
    config = load_config()
    data = load_model_dataset()
    test = select_ids(data, read_ids("test_ids.csv"), "test_ids.csv")
    normalisation = json.loads((RESULTS_DIR / "mcda_normalisation.json").read_text(encoding="utf-8"))
    selection = json.loads((RESULTS_DIR / "mcda_threshold_selection.json").read_text(encoding="utf-8"))
    threshold = float(selection["selected_threshold"])
    components = mcda_components(test, normalisation)
    scores = mcda_scores(components, config)
    predictions = (scores >= threshold).astype(int)
    target = config["target"]["name"]
    output_dir = RESULTS_DIR / "model_predictions"
    output_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "site_id": test["site_id"], "proxy_label": test[target].astype(int),
        "weighted_mcda_score": scores, "weighted_mcda_prediction": predictions,
    }).to_csv(output_dir / "weighted_mcda_predictions.csv", index=False)
    component_output = pd.concat(
        [test[["site_id", target]].rename(columns={target: "proxy_label"}).reset_index(drop=True), components.reset_index(drop=True)],
        axis=1,
    )
    component_output.to_csv(output_dir / "weighted_mcda_components.csv", index=False)
    metrics = calculate_metrics(test[target], scores, predictions)
    write_json(RESULTS_DIR / "weighted_mcda_metrics.json", {
        "method": "fixed-weight MCDA (not AHP)", "threshold": threshold,
        "threshold_source": "development-set F1 selection", **metrics,
    })
    print(metrics)


if __name__ == "__main__":
    main()

