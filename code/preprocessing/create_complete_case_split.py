"""Create the deterministic split for rows with six valid ordinal soil values."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import RESULTS_DIR, SPLITS_DIR, load_config, load_site_features, write_json


def main() -> None:
    config = load_config()
    data = load_site_features()
    soil = config["features"]["soil_columns"]
    complete = data.loc[data[soil].apply(lambda column: column.between(1, 8)).all(axis=1)].copy()
    train, test = train_test_split(
        complete["site_id"].astype("string"), test_size=float(config["splits"]["test_size"]),
        random_state=int(config["splits"]["random_state"]), stratify=complete["prefab_label"]
    )
    train, test = train.reset_index(drop=True), test.reset_index(drop=True)
    pd.DataFrame({"site_id": train}).to_csv(SPLITS_DIR / "complete_case_train_ids.csv", index=False)
    pd.DataFrame({"site_id": test}).to_csv(SPLITS_DIR / "complete_case_test_ids.csv", index=False)
    write_json(RESULTS_DIR / "complete_case_split_summary.json", {
        "definition": "all six LSC fields are ordinary values in 1-8",
        "random_state": int(config["splits"]["random_state"]), "stratified": True,
        "rows": int(len(complete)), "train_rows": int(len(train)), "test_rows": int(len(test)),
        "class_counts": {str(k): int(v) for k, v in complete["prefab_label"].value_counts().sort_index().items()},
    })
    print(f"Complete case: {len(complete):,} rows; {len(train):,}/{len(test):,} split")


if __name__ == "__main__":
    main()

