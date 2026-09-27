"""Create the deterministic west-to-east sensitivity split in EPSG:7856."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from shapely import wkt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import RESULTS_DIR, SPLITS_DIR, load_config, load_site_features, write_json


def main() -> None:
    config = load_config()
    data = load_site_features()
    threshold = float(config["splits"]["spatial_easting_threshold_m"])
    easting = data["geometry"].map(lambda value: float(wkt.loads(value).x))
    split = pd.DataFrame({
        "site_id": data["site_id"].astype("string"), "easting_m": easting,
        "split": pd.Series("east_test", index=data.index),
    })
    split.loc[easting <= threshold, "split"] = "west_train"
    split.to_csv(SPLITS_DIR / "spatial_split_ids.csv", index=False)
    write_json(RESULTS_DIR / "spatial_split_summary.json", {
        "crs": config["study"]["projected_crs"], "coordinate": "geometry x/easting",
        "threshold_m": threshold, "rule": config["splits"]["spatial_rule"],
        "west_train_rows": int(split["split"].eq("west_train").sum()),
        "east_test_rows": int(split["split"].eq("east_test").sum()),
        "interpretation": "directional internal sensitivity check, not external validation",
    })
    print(split["split"].value_counts().to_dict())


if __name__ == "__main__":
    main()
