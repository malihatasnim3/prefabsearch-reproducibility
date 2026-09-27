"""Fit development-only imputers and materialise the shared model matrix."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import (
    PROCESSED_DIR,
    RESULTS_DIR,
    apply_feature_imputation,
    fit_feature_imputation,
    load_config,
    load_site_features,
    read_ids,
    select_ids,
    write_json,
)


def main() -> None:
    config = load_config()
    source = load_site_features()
    train_ids, test_ids = read_ids("train_ids.csv"), read_ids("test_ids.csv")
    train_raw = select_ids(source, train_ids, "train_ids.csv")
    imputation = fit_feature_imputation(train_raw, config)
    model = apply_feature_imputation(source, imputation, config)
    features = config["features"]["columns"]
    target = config["target"]["name"]
    output = model[["site_id", "geometry", *features, target]].copy()
    if output[[*features, target]].isna().any().any():
        raise ValueError("Missing values remain after development-only imputation")
    output.to_csv(PROCESSED_DIR / "model_dataset.csv", index=False)
    select_ids(output, train_ids, "train_ids.csv").to_csv(PROCESSED_DIR / "train_dataset.csv", index=False)
    select_ids(output, test_ids, "test_ids.csv").to_csv(PROCESSED_DIR / "test_dataset.csv", index=False)
    write_json(RESULTS_DIR / "imputation_values.json", {
        **imputation,
        "fit_scope": "development rows only",
        "train_rows": int(len(train_ids)),
        "test_rows": int(len(test_ids)),
        "application": "same fitted values applied to development and held-out rows",
    })
    print(f"Prepared {len(output):,} model rows")


if __name__ == "__main__":
    main()

