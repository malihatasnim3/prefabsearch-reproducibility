"""Shared, release-local scientific utilities for PrefabSearch."""

from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd
import yaml
from lightgbm import LGBMClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.neural_network import MLPClassifier

# scikit-learn 1.6 can emit transient overflow/divide warnings from its private
# matrix-multiplication helper while Adam adapts the learning rate. The fitted
# estimator remains finite and is explicitly validated through its probabilities.
warnings.filterwarnings("ignore", category=RuntimeWarning, module=r"sklearn\.utils\.extmath")


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "research_config.yaml"
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = ROOT / "results"
MODEL_DIR = ROOT / "models"
SPLITS_DIR = ROOT / "splits"
FIGURES_DIR = ROOT / "figures"
WATER_SPECIAL_CODE = "WATER_SPECIAL_CODE"


def load_config() -> dict[str, Any]:
    return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))


def ensure_directories() -> None:
    for path in (PROCESSED_DIR, RESULTS_DIR, MODEL_DIR, SPLITS_DIR, FIGURES_DIR):
        path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_columns(frame: pd.DataFrame, columns: Iterable[str], name: str) -> None:
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def clean_soil_code(value: object) -> float | str:
    """Interpret one raw NSW LSC code without coercing special values."""
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return float("nan")
    if not np.isfinite(numeric):
        return float("nan")
    if 1.0 <= numeric <= 8.0:
        return numeric
    if numeric == 98.0:
        return float("nan")
    if numeric == 99.0:
        return WATER_SPECIAL_CODE
    return float("nan")


def soil_special_masks(frame: pd.DataFrame, soil_columns: list[str]) -> tuple[pd.Series, pd.Series]:
    numeric = frame[soil_columns].apply(pd.to_numeric, errors="coerce")
    return numeric.eq(98.0).any(axis=1), numeric.eq(99.0).any(axis=1)


def clean_soil_frame(frame: pd.DataFrame, soil_columns: list[str]) -> pd.DataFrame:
    cleaned = frame.copy()
    for column in soil_columns:
        numeric = pd.to_numeric(cleaned[column], errors="coerce")
        cleaned[column] = numeric.where(numeric.between(1.0, 8.0))
    return cleaned


def raw_ground_difficulty(frame: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    weights = config["features"]["ground_difficulty_weights"]
    weighted = pd.Series(0.0, index=frame.index)
    available = pd.Series(0.0, index=frame.index)
    for column, weight in weights.items():
        valid = pd.to_numeric(frame[column], errors="coerce").where(
            pd.to_numeric(frame[column], errors="coerce").between(1.0, 8.0)
        )
        normalized = (valid - 1.0) / 7.0
        present = normalized.notna()
        weighted = weighted.add(normalized.fillna(0.0) * float(weight), fill_value=0.0)
        available = available.add(present.astype(float) * float(weight), fill_value=0.0)
    return (weighted / available.replace(0.0, np.nan)).clip(0.0, 1.0)


def proxy_labels(frame: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    rule = config["target"]
    return (
        (frame["slope"] < float(rule["slope_threshold_deg"]))
        & (frame["road_distance_m"] < float(rule["road_distance_threshold_m"]))
        & (frame["ground_difficulty_score"] < float(rule["ground_difficulty_threshold"]))
    ).astype(int)


def read_ids(name: str) -> pd.Series:
    path = SPLITS_DIR / name
    frame = pd.read_csv(path, dtype={"site_id": "string"})
    require_columns(frame, ["site_id"], name)
    if frame["site_id"].isna().any() or frame["site_id"].duplicated().any():
        raise ValueError(f"{name} contains missing or duplicate site IDs")
    return frame["site_id"]


def select_ids(frame: pd.DataFrame, ids: pd.Series, source_name: str) -> pd.DataFrame:
    source = frame.copy()
    source["site_id"] = source["site_id"].astype("string")
    if source["site_id"].isna().any() or source["site_id"].duplicated().any():
        raise ValueError("Source data must have complete unique site IDs")
    selected = pd.DataFrame({"site_id": ids.astype("string")}).merge(
        source, on="site_id", how="left", validate="one_to_one", indicator=True
    )
    if not selected["_merge"].eq("both").all():
        raise ValueError(f"{source_name} contains IDs absent from the dataset")
    return selected.drop(columns="_merge")


def load_site_features() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "site_features.csv", dtype={"site_id": "string"})


def load_model_dataset() -> pd.DataFrame:
    return pd.read_csv(PROCESSED_DIR / "model_dataset.csv", dtype={"site_id": "string"})


def fit_feature_imputation(train: pd.DataFrame, config: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    for column in config["features"]["soil_columns"]:
        valid = pd.to_numeric(train[column], errors="coerce").where(
            pd.to_numeric(train[column], errors="coerce").between(1.0, 8.0)
        )
        if not valid.notna().any():
            raise ValueError(f"No valid development values available for {column}")
        values[column] = float(valid.median())
    observed_ground = train["ground_difficulty_score_raw"].dropna()
    if observed_ground.empty:
        raise ValueError("No valid development ground scores are available")
    values["ground_difficulty_score"] = float(observed_ground.median())
    return values


def apply_feature_imputation(frame: pd.DataFrame, values: dict[str, float], config: dict[str, Any]) -> pd.DataFrame:
    result = frame.copy()
    for column in config["features"]["soil_columns"]:
        valid = pd.to_numeric(result[column], errors="coerce").where(
            pd.to_numeric(result[column], errors="coerce").between(1.0, 8.0)
        )
        result[column] = valid.fillna(float(values[column]))
    result["ground_difficulty_score"] = result["ground_difficulty_score_raw"].fillna(
        float(values["ground_difficulty_score"])
    )
    return result


def fit_mcda_normalisation(train: pd.DataFrame) -> dict[str, float]:
    return {
        "slope_min": float(train["slope"].min()),
        "slope_max": float(train["slope"].max()),
        "road_distance_min": float(train["road_distance_m"].min()),
        "road_distance_max": float(train["road_distance_m"].max()),
        "reference": "development rows only",
        "out_of_range_policy": "clip transformed target values to [0, 1]",
    }


def _reverse_minmax(values: pd.Series, low: float, high: float) -> pd.Series:
    if high == low:
        return pd.Series(1.0, index=values.index)
    return (1.0 - (values - low) / (high - low)).clip(0.0, 1.0)


def mcda_components(frame: pd.DataFrame, normalisation: dict[str, float]) -> pd.DataFrame:
    components = pd.DataFrame(index=frame.index)
    components["slope_score"] = _reverse_minmax(
        frame["slope"], normalisation["slope_min"], normalisation["slope_max"]
    )
    components["road_access_score"] = _reverse_minmax(
        frame["road_distance_m"], normalisation["road_distance_min"], normalisation["road_distance_max"]
    )
    components["ground_score"] = (1.0 - frame["ground_difficulty_score"]).clip(0.0, 1.0)
    mapping = {
        "erosion_score": "LSC_WatrEr",
        "waterlogging_score": "LSC_Watlog",
        "mass_movement_score": "LSC_Mass_m",
        "shallow_rock_score": "LSC_Sh_Rk",
        "structure_decline_score": "LSC_StrD",
    }
    for score_name, feature_name in mapping.items():
        components[score_name] = (1.0 - (frame[feature_name] - 1.0) / 7.0).clip(0.0, 1.0)
    return components


def mcda_scores(components: pd.DataFrame, config: dict[str, Any]) -> pd.Series:
    weights = config["models"]["weighted_mcda"]["weights"]
    return sum(components[column] * float(weight) for column, weight in weights.items())


def select_f1_threshold(scores: pd.Series, labels: pd.Series) -> tuple[float, dict[str, Any]]:
    records: list[tuple[float, float, float]] = []
    for threshold in np.unique(scores.to_numpy(dtype=float)):
        prediction = (scores >= threshold).astype(int)
        records.append(
            (
                float(f1_score(labels, prediction, zero_division=0)),
                float(accuracy_score(labels, prediction)),
                float(threshold),
            )
        )
    best = max(records, key=lambda row: (row[0], row[1], -row[2]))
    return best[2], {
        "selected_threshold": best[2],
        "development_f1": best[0],
        "development_accuracy": best[1],
        "candidate_thresholds_evaluated": len(records),
        "tie_breaking_rule": "maximum F1, then maximum accuracy, then lowest threshold",
    }


def calculate_metrics(labels: pd.Series | np.ndarray, probabilities: pd.Series | np.ndarray, predictions: pd.Series | np.ndarray) -> dict[str, Any]:
    return {
        "n": int(len(labels)),
        "accuracy": float(accuracy_score(labels, predictions)),
        "precision": float(precision_score(labels, predictions, zero_division=0)),
        "recall": float(recall_score(labels, predictions, zero_division=0)),
        "f1": float(f1_score(labels, predictions, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "average_precision": float(average_precision_score(labels, probabilities)),
        "confusion_matrix": confusion_matrix(labels, predictions).tolist(),
    }


def build_lightgbm(config: dict[str, Any], *, random_state: int | None = None) -> LGBMClassifier:
    settings = config["models"]["lightgbm"]
    return LGBMClassifier(
        objective="binary",
        random_state=int(settings["random_state"] if random_state is None else random_state),
        class_weight=settings["class_weight"],
        verbosity=-1,
        n_estimators=int(settings["n_estimators"]),
        learning_rate=float(settings["learning_rate"]),
        num_leaves=int(settings["num_leaves"]),
        max_depth=int(settings["max_depth"]),
        min_child_samples=int(settings["min_child_samples"]),
        reg_lambda=float(settings["reg_lambda"]),
    )


def build_mlp(config: dict[str, Any], *, random_state: int | None = None) -> MLPClassifier:
    settings = config["models"]["mlp"]
    return MLPClassifier(
        hidden_layer_sizes=tuple(settings["hidden_layer_sizes"]),
        activation=settings["activation"],
        solver=settings["solver"],
        alpha=float(settings["alpha"]),
        batch_size=int(settings["batch_size"]),
        learning_rate=settings["learning_rate"],
        learning_rate_init=float(settings["learning_rate_init"]),
        max_iter=int(settings["max_iter"]),
        early_stopping=bool(settings["early_stopping"]),
        validation_fraction=float(settings["validation_fraction"]),
        n_iter_no_change=int(settings["n_iter_no_change"]),
        random_state=int(settings["random_state"] if random_state is None else random_state),
    )


def save_joblib(value: Any, name: str) -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(value, MODEL_DIR / name)
