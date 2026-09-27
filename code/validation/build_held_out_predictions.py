"""Build one held-out table through validated one-to-one site-ID joins."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import RESULTS_DIR, read_ids, require_columns


def load_prediction(name: str, columns: list[str]) -> pd.DataFrame:
    path = RESULTS_DIR / "model_predictions" / name
    frame = pd.read_csv(path, dtype={"site_id": "string"})
    require_columns(frame, ["site_id", "proxy_label", *columns], name)
    if frame["site_id"].isna().any() or frame["site_id"].duplicated().any():
        raise ValueError(f"{name} has missing or duplicate site IDs")
    return frame[["site_id", "proxy_label", *columns]]


def main() -> None:
    mcda = load_prediction("weighted_mcda_predictions.csv", ["weighted_mcda_score", "weighted_mcda_prediction"])
    lightgbm = load_prediction("gradient_boosting_predictions.csv", ["lightgbm_probability", "lightgbm_prediction"])
    mlp = load_prediction("mlp_predictions.csv", ["mlp_probability", "mlp_prediction"])
    merged = mcda.merge(lightgbm, on="site_id", how="outer", validate="one_to_one", suffixes=("_mcda", "_lightgbm"))
    if merged.isna().any().any():
        raise ValueError("A method is missing for one or more held-out sites")
    if not merged["proxy_label_mcda"].equals(merged["proxy_label_lightgbm"]):
        raise ValueError("MCDA and LightGBM targets disagree")
    merged = merged.rename(columns={"proxy_label_mcda": "proxy_label"}).drop(columns="proxy_label_lightgbm")
    merged = merged.merge(mlp, on="site_id", how="outer", validate="one_to_one", suffixes=("", "_mlp"))
    if merged.isna().any().any() or not merged["proxy_label"].equals(merged["proxy_label_mlp"]):
        raise ValueError("MLP predictions are missing or target values disagree")
    merged = merged.drop(columns="proxy_label_mlp")
    test_ids = read_ids("test_ids.csv")
    if set(merged["site_id"]) != set(test_ids):
        raise ValueError("Combined prediction IDs do not equal the held-out split")
    merged = pd.DataFrame({"site_id": test_ids}).merge(merged, on="site_id", validate="one_to_one")
    merged.to_csv(RESULTS_DIR / "held_out_predictions.csv", index=False)
    print(f"Wrote {len(merged):,} held-out predictions")


if __name__ == "__main__":
    main()

