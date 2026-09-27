"""Fit MCDA scaling and select its binary threshold on development rows only."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    RESULTS_DIR,
    fit_mcda_normalisation,
    load_config,
    load_model_dataset,
    mcda_components,
    mcda_scores,
    read_ids,
    select_f1_threshold,
    select_ids,
    write_json,
)


def main() -> None:
    config = load_config()
    data = load_model_dataset()
    train = select_ids(data, read_ids("train_ids.csv"), "train_ids.csv")
    normalisation = fit_mcda_normalisation(train)
    components = mcda_components(train, normalisation)
    scores = mcda_scores(components, config)
    threshold, selection = select_f1_threshold(scores, train[config["target"]["name"]])
    write_json(RESULTS_DIR / "mcda_normalisation.json", normalisation)
    write_json(RESULTS_DIR / "mcda_threshold_selection.json", {
        **selection,
        "selection_data": "development rows only",
        "development_rows": int(len(train)),
        "normalisation_parameters": normalisation,
    })
    print(f"Selected MCDA threshold {threshold:.15f}")


if __name__ == "__main__":
    main()
