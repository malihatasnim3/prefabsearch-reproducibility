#!/usr/bin/env python3
"""Independent validation of the corrected, self-contained reproducibility release."""

from __future__ import annotations

import json
import re
import sys
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from pypdf import PdfReader
from shapely import wkt
from sklearn.inspection import permutation_importance
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split

warnings.filterwarnings(
    "ignore", category=FutureWarning,
    message=r"The LGBMClassifier or classes from which it inherits use .*",
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from common import (  # noqa: E402
    MODEL_DIR,
    PROCESSED_DIR,
    RESULTS_DIR,
    SOURCE_DIR,
    SPLITS_DIR,
    apply_feature_imputation,
    calculate_metrics,
    clean_soil_frame,
    fit_feature_imputation,
    fit_mcda_normalisation,
    load_config,
    mcda_components,
    mcda_scores,
    proxy_labels,
    raw_ground_difficulty,
    select_f1_threshold,
    select_ids,
    soil_special_masks,
    write_json,
)
sys.path.insert(0, str(ROOT / "code" / "validation"))
from evaluate_models import boundary_analysis  # noqa: E402

TOL = 1e-10


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_close(actual: float, expected: float, *, atol: float = TOL) -> None:
    if not np.isclose(float(actual), float(expected), rtol=1e-9, atol=atol):
        raise AssertionError(f"{actual!r} != {expected!r}")


def compare_metric_record(actual: dict, expected: dict) -> None:
    for key in ("n", "accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"):
        if key == "n":
            if int(actual[key]) != int(expected[key]):
                raise AssertionError(f"n differs: {actual[key]} != {expected[key]}")
        else:
            assert_close(actual[key], expected[key])
    if np.asarray(actual["confusion_matrix"]).tolist() != np.asarray(expected["confusion_matrix"]).tolist():
        raise AssertionError("confusion matrices differ")


def independent_main_rebuild(config: dict) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    source = pd.read_csv(SOURCE_DIR / "analysis_grid_with_raw_lsc_codes.csv", dtype={"site_id": "string"})
    soil = config["features"]["soil_columns"]
    code98, water = soil_special_masks(source, soil)
    clean = clean_soil_frame(source.loc[~water].copy(), soil)
    clean["slope"] = pd.to_numeric(clean["slope"], errors="coerce")
    clean["road_distance_m"] = pd.to_numeric(clean["road_distance_m"], errors="coerce")
    clean = clean.loc[clean.slope.notna() & clean.road_distance_m.notna() & clean.slope.ge(0) & clean.road_distance_m.ge(0)].copy()
    clean["ground_difficulty_score_raw"] = raw_ground_difficulty(clean, config)
    clean["soil_valid_component_count"] = clean[soil].notna().sum(axis=1).astype(int)
    clean["soil_missing"] = clean.soil_valid_component_count.eq(0).astype(int)
    clean["complete_case_soil"] = clean[soil].apply(lambda c: c.between(1, 8)).all(axis=1).astype(int)
    clean["special_code_98"] = source.loc[~water, soil].apply(pd.to_numeric, errors="coerce").eq(98).any(axis=1).astype(int).to_numpy()
    clean["ground_difficulty_score"] = clean.ground_difficulty_score_raw.fillna(float(clean.ground_difficulty_score_raw.median()))
    clean["prefab_label"] = proxy_labels(clean, config)
    for _iteration in range(10):
        train_ids, test_ids = train_test_split(
            clean.site_id.astype("string"), test_size=float(config["splits"]["test_size"]),
            random_state=int(config["splits"]["random_state"]), stratify=clean.prefab_label,
        )
        train_ids, test_ids = train_ids.reset_index(drop=True), test_ids.reset_index(drop=True)
        train = clean.loc[clean.site_id.isin(set(train_ids))]
        median = float(train.ground_difficulty_score_raw.dropna().median())
        new_score = clean.ground_difficulty_score_raw.fillna(median)
        candidate = clean.copy(); candidate["ground_difficulty_score"] = new_score
        new_label = proxy_labels(candidate, config)
        if new_label.equals(clean.prefab_label):
            clean["ground_difficulty_score"] = new_score
            clean["prefab_label"] = new_label
            break
        clean["ground_difficulty_score"] = new_score
        clean["prefab_label"] = new_label
    else:
        raise AssertionError("independent fixed-point split did not converge")
    clean["ground_score_imputed"] = clean.ground_difficulty_score_raw.isna().astype(int)
    return clean, train_ids, test_ids, water


def check_dataset_and_splits() -> None:
    config = load_config()
    rebuilt, train_ids, test_ids, water = independent_main_rebuild(config)
    released = pd.read_csv(PROCESSED_DIR / "site_features.csv", dtype={"site_id": "string"})
    if len(rebuilt) != len(released) or len(released) != 21217:
        raise AssertionError("corrected final row count is not 21,217")
    pd.testing.assert_frame_equal(
        rebuilt[released.columns].reset_index(drop=True), released.reset_index(drop=True),
        check_dtype=False, check_exact=False, rtol=1e-10, atol=1e-12,
    )
    source = pd.read_csv(SOURCE_DIR / "analysis_grid_with_raw_lsc_codes.csv", dtype={"site_id": "string"})
    soil = config["features"]["soil_columns"]
    code98, source_water = soil_special_masks(source, soil)
    if int(source_water.sum()) != 9 or int(code98.sum()) != 81:
        raise AssertionError("raw special-code counts differ from 9 water / 81 not-assessed")
    if set(source.loc[source_water, "site_id"]) & set(released.site_id):
        raise AssertionError("water-coded sites remain in the final dataset")
    if int(released.special_code_98.sum()) != 81 or int(released.soil_missing.sum()) != 18030:
        raise AssertionError("code-98 or soil-missing counts differ")
    for column in soil:
        valid = released[column].dropna()
        if not valid.between(1, 8).all():
            raise AssertionError(f"{column} retains a non-ordinary code")
    expected_train = pd.read_csv(SPLITS_DIR / "train_ids.csv", dtype={"site_id": "string"}).site_id
    expected_test = pd.read_csv(SPLITS_DIR / "test_ids.csv", dtype={"site_id": "string"}).site_id
    if not train_ids.equals(expected_train) or not test_ids.equals(expected_test):
        raise AssertionError("main split IDs do not reproduce exactly")
    if set(expected_train) & set(expected_test) or set(expected_train) | set(expected_test) != set(released.site_id):
        raise AssertionError("main split is not a disjoint exact partition")
    complete = released.loc[released[soil].apply(lambda c: c.between(1, 8)).all(axis=1)]
    ctrain, ctest = train_test_split(
        complete.site_id.astype("string"), test_size=float(config["splits"]["test_size"]),
        random_state=int(config["splits"]["random_state"]), stratify=complete.prefab_label,
    )
    ctrain, ctest = ctrain.reset_index(drop=True), ctest.reset_index(drop=True)
    saved_ctrain = pd.read_csv(SPLITS_DIR / "complete_case_train_ids.csv", dtype={"site_id": "string"}).site_id
    saved_ctest = pd.read_csv(SPLITS_DIR / "complete_case_test_ids.csv", dtype={"site_id": "string"}).site_id
    if len(complete) != 3187 or not ctrain.equals(saved_ctrain) or not ctest.equals(saved_ctest):
        raise AssertionError("complete-case subset or split does not reproduce")
    threshold = float(config["splits"]["spatial_easting_threshold_m"])
    spatial = pd.read_csv(SPLITS_DIR / "spatial_split_ids.csv", dtype={"site_id": "string"})
    eastings = released.geometry.map(lambda value: float(wkt.loads(value).x))
    expected = np.where(eastings <= threshold, "west_train", "east_test")
    if not np.array_equal(spatial.site_id.to_numpy(), released.site_id.to_numpy()) or not np.array_equal(spatial.split.to_numpy(), expected):
        raise AssertionError("spatial split does not reproduce from geometry")


def check_development_fit_and_models() -> None:
    config = load_config(); features = config["features"]["columns"]; target = config["target"]["name"]
    raw = pd.read_csv(PROCESSED_DIR / "site_features.csv", dtype={"site_id": "string"})
    model_data = pd.read_csv(PROCESSED_DIR / "model_dataset.csv", dtype={"site_id": "string"})
    train_ids = pd.read_csv(SPLITS_DIR / "train_ids.csv", dtype={"site_id": "string"}).site_id
    test_ids = pd.read_csv(SPLITS_DIR / "test_ids.csv", dtype={"site_id": "string"}).site_id
    raw_train = select_ids(raw, train_ids, "main development IDs")
    data_train = select_ids(model_data, train_ids, "main development IDs")
    data_test = select_ids(model_data, test_ids, "main held-out IDs")
    imputation = fit_feature_imputation(raw_train, config)
    stored_imputation = load_json(RESULTS_DIR / "imputation_values.json")
    for key, value in imputation.items(): assert_close(value, stored_imputation[key])
    independently_imputed = apply_feature_imputation(raw, imputation, config)
    pd.testing.assert_frame_equal(
        independently_imputed[["site_id", *features]].reset_index(drop=True),
        model_data[["site_id", *features]].reset_index(drop=True), check_dtype=False,
        check_exact=False, rtol=1e-10, atol=1e-12,
    )
    norm = fit_mcda_normalisation(data_train); stored_norm = load_json(RESULTS_DIR / "mcda_normalisation.json")
    for key in ("slope_min", "slope_max", "road_distance_min", "road_distance_max"): assert_close(norm[key], stored_norm[key])
    development_scores = mcda_scores(mcda_components(data_train, norm), config)
    threshold, _ = select_f1_threshold(development_scores, data_train[target].astype(int))
    stored_threshold = load_json(RESULTS_DIR / "mcda_threshold_selection.json")["selected_threshold"]
    assert_close(threshold, stored_threshold)
    held = pd.read_csv(RESULTS_DIR / "held_out_predictions.csv", dtype={"site_id": "string"})
    if not held.site_id.equals(test_ids) or not held.proxy_label.equals(data_test[target].astype(int)):
        raise AssertionError("held-out predictions are not a one-to-one join in fixed test-ID order")
    mcda_probability = mcda_scores(mcda_components(data_test, norm), config).to_numpy()
    if not np.allclose(mcda_probability, held.weighted_mcda_score, rtol=1e-10, atol=1e-12):
        raise AssertionError("MCDA held-out scores do not reproduce")
    lightgbm = joblib.load(MODEL_DIR / "gradient_boosting.joblib")
    gb_probability = lightgbm.predict_proba(data_test[features])[:, 1]
    if not np.allclose(gb_probability, held.lightgbm_probability, rtol=1e-10, atol=1e-12):
        raise AssertionError("LightGBM held-out probabilities do not reproduce")
    scaler = joblib.load(MODEL_DIR / "mlp_scaler.joblib")
    if not np.allclose(scaler.mean_, data_train[features].to_numpy().mean(axis=0), rtol=1e-10, atol=1e-12):
        raise AssertionError("MLP scaler mean is not development-fitted")
    if not np.allclose(scaler.var_, data_train[features].to_numpy().var(axis=0), rtol=1e-10, atol=1e-12):
        raise AssertionError("MLP scaler variance is not development-fitted")
    mlp = joblib.load(MODEL_DIR / "mlp.joblib")
    mlp_probability = mlp.predict_proba(scaler.transform(data_test[features]))[:, 1]
    if not np.allclose(mlp_probability, held.mlp_probability, rtol=1e-9, atol=1e-12):
        raise AssertionError("MLP held-out probabilities do not reproduce")
    probability_map = {
        "weighted_mcda": (mcda_probability, float(stored_threshold)),
        "gradient_boosting": (gb_probability, 0.5), "mlp": (mlp_probability, 0.5),
    }
    verified = load_json(RESULTS_DIR / "verified_metrics.json")["held_out"]
    for method, (probability, cutoff) in probability_map.items():
        actual = calculate_metrics(data_test[target].astype(int), probability, (probability >= cutoff).astype(int))
        compare_metric_record(actual, verified[method])
    code = (ROOT / "code/modeling/train_gradient_boosting.py").read_text() + (ROOT / "code/common.py").read_text()
    if "class_weight" not in code or "compute_sample_weight" in code or re.search(r"\.fit\([^\n]*sample_weight", code):
        raise AssertionError("LightGBM does not use exactly one class-balancing mechanism")


def check_prediction_metrics(path: Path, label: str, methods: dict[str, tuple[str, str]], expected: dict) -> None:
    frame = pd.read_csv(path, dtype={"site_id": "string"})
    for method, (score, prediction) in methods.items():
        actual = calculate_metrics(frame[label], frame[score], frame[prediction])
        compare_metric_record(actual, expected[method])


def check_robustness() -> None:
    config = load_config()
    complete = load_json(RESULTS_DIR / "complete_case_soil_results.json")
    check_prediction_metrics(
        RESULTS_DIR / "complete_case_soil_predictions.csv", "y_true",
        {"weighted_mcda": ("weighted_mcda_score", "weighted_mcda_prediction"),
         "lightgbm": ("lightgbm_probability", "lightgbm_prediction"),
         "mlp": ("mlp_probability", "mlp_prediction")}, complete["evaluation"],
    )
    spatial = load_json(RESULTS_DIR / "spatial_validation_results.json")
    check_prediction_metrics(RESULTS_DIR / "spatial_validation_predictions.csv", "y_true",
                             {"spatial": ("probability", "prediction")}, {"spatial": spatial})
    shuffled = load_json(RESULTS_DIR / "shuffled_label_results.json")
    check_prediction_metrics(RESULTS_DIR / "shuffled_label_predictions.csv", "y_true",
                             {"shuffled": ("probability", "prediction")}, {"shuffled": shuffled})
    model_data = pd.read_csv(PROCESSED_DIR / "model_dataset.csv", dtype={"site_id": "string"})
    shuffled_predictions = pd.read_csv(RESULTS_DIR / "shuffled_label_predictions.csv", dtype={"site_id": "string"})
    rng = np.random.default_rng(int(config["robustness"]["shuffled_label_seed"]))
    shuffled_map = pd.Series(rng.permutation(model_data[config["target"]["name"]].to_numpy()), index=model_data.site_id)
    if not np.array_equal(shuffled_predictions.y_true, shuffled_predictions.site_id.map(shuffled_map).astype(int)):
        raise AssertionError("shuffled-label target does not reproduce while features remain fixed")
    cv = pd.read_csv(RESULTS_DIR / "lightgbm_cv_predictions.csv", dtype={"site_id": "string"})
    train_ids = pd.read_csv(SPLITS_DIR / "train_ids.csv", dtype={"site_id": "string"}).site_id
    test_ids = pd.read_csv(SPLITS_DIR / "test_ids.csv", dtype={"site_id": "string"}).site_id
    if cv.site_id.duplicated().any() or set(cv.site_id) != set(train_ids) or set(cv.site_id) & set(test_ids):
        raise AssertionError("cross-validation is not confined to the development partition")
    cv_json = load_json(RESULTS_DIR / "lightgbm_cv_summary.json")
    for fold in range(1, 6):
        part = cv.loc[cv.fold.eq(fold)]
        actual = calculate_metrics(part.y_true, part.probability, part.prediction)
        compare_metric_record(actual, cv_json["folds"][fold - 1])
    for key in ("accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"):
        values = np.asarray([row[key] for row in cv_json["folds"]])
        assert_close(values.mean(), cv_json["summary"][key]["mean"])
        assert_close(values.std(), cv_json["summary"][key]["std"])
    scenarios = pd.read_csv(RESULTS_DIR / "mcda_weight_sensitivity_scenarios.csv")
    sensitivity = load_json(RESULTS_DIR / "mcda_weight_sensitivity.json")
    if len(scenarios) != int(config["robustness"]["mcda_weight_scenarios"]):
        raise AssertionError("MCDA sensitivity run count differs")
    for column in scenarios.columns:
        values = scenarios[column].to_numpy(dtype=float)
        for key, value in {"p05": np.quantile(values, .05), "median": np.median(values), "p95": np.quantile(values, .95)}.items():
            assert_close(value, sensitivity["summary"][column][key])
    components = pd.read_csv(RESULTS_DIR / "model_predictions/weighted_mcda_components.csv")
    columns = list(config["models"]["weighted_mcda"]["weights"])
    base_weights = np.asarray([config["models"]["weighted_mcda"]["weights"][c] for c in columns])
    x = components[columns].to_numpy(); y = components.proxy_label.to_numpy(dtype=int)
    threshold = float(load_json(RESULTS_DIR / "mcda_threshold_selection.json")["selected_threshold"])
    base_score = np.sum(x * base_weights, axis=1); base_prediction = (base_score >= threshold).astype(int)
    base_rank = pd.Series(base_score).rank(method="average")
    rng = np.random.default_rng(int(config["robustness"]["mcda_weight_seed"])); independent = []
    fraction = float(config["robustness"]["mcda_weight_perturbation_fraction"])
    for _ in range(len(scenarios)):
        weights = base_weights * rng.uniform(1 - fraction, 1 + fraction, len(base_weights)); weights /= weights.sum()
        score = np.sum(x * weights, axis=1); prediction = (score >= threshold).astype(int)
        independent.append((base_rank.corr(pd.Series(score).rank(method="average")), np.count_nonzero(prediction != base_prediction), prediction.sum(), f1_score(y, prediction, zero_division=0)))
    if not np.allclose(np.asarray(independent), scenarios.to_numpy(dtype=float), rtol=1e-9, atol=1e-12):
        raise AssertionError("MCDA perturbation scenarios do not reproduce")
    held = pd.read_csv(RESULTS_DIR / "held_out_predictions.csv", dtype={"site_id": "string"})
    expected_boundary = boundary_analysis(held, config).reset_index(drop=True)
    saved_boundary = pd.read_csv(RESULTS_DIR / "boundary_analysis.csv").reset_index(drop=True)
    pd.testing.assert_frame_equal(expected_boundary, saved_boundary, check_dtype=False,
                                  check_exact=False, rtol=1e-10, atol=1e-12)
    features = config["features"]["columns"]
    test_ids = pd.read_csv(SPLITS_DIR / "test_ids.csv", dtype={"site_id": "string"}).site_id
    test = select_ids(model_data, test_ids, "held-out IDs")
    repeats = int(config["robustness"]["permutation_repeats"]); seed = int(config["robustness"]["permutation_seed"])
    stored = pd.read_csv(RESULTS_DIR / "permutation_importance.csv").sort_values(["method", "feature"]).reset_index(drop=True)
    recomputed = []
    scaler = joblib.load(MODEL_DIR / "mlp_scaler.joblib")
    for name, model, values in [
        ("LightGBM", joblib.load(MODEL_DIR / "gradient_boosting.joblib"), test[features]),
        ("MLP", joblib.load(MODEL_DIR / "mlp.joblib"), scaler.transform(test[features])),
    ]:
        p = permutation_importance(model, values, test[config["target"]["name"]].astype(int), scoring="f1", n_repeats=repeats, random_state=seed, n_jobs=1)
        for feature, mean, std in zip(features, p.importances_mean, p.importances_std, strict=True):
            recomputed.append((name, feature, mean, std))
    expected = pd.DataFrame(recomputed, columns=["method", "feature", "importance_mean", "importance_std"]).sort_values(["method", "feature"]).reset_index(drop=True)
    if not stored[["method", "feature"]].equals(expected[["method", "feature"]]) or not np.allclose(stored[["importance_mean", "importance_std"]], expected[["importance_mean", "importance_std"]], rtol=1e-9, atol=1e-12):
        raise AssertionError("permutation importance does not reproduce")


def check_artifacts_and_portability() -> None:
    required = [
        "README.md", "requirements.txt", "LICENSE", "CITATION.cff",
        "metadata/DATA_SOURCES.md", "metadata/DATA_DICTIONARY.md",
        "metadata/SOURCE_FILE_MANIFEST.csv", "metadata/LICENSE_NOTES.md",
        "metadata/DERIVED_DATA_LICENSE_REVIEW.md", "MANUSCRIPT_RESULT_CHANGE_REPORT.md",
        "FINAL_RELEASE_REPORT.md",
    ]
    missing = [item for item in required if not (ROOT / item).is_file()]
    if missing: raise AssertionError(f"required release documentation is missing: {missing}")
    for index in range(1, 7):
        pdfs = list((ROOT / "figures").glob(f"Figure_{index}_*.pdf")); pngs = list((ROOT / "figures").glob(f"Figure_{index}_*.png"))
        if len(pdfs) != 1 or len(pngs) != 1 or pngs[0].stat().st_size < 10_000:
            raise AssertionError(f"Figure {index} output pair is missing or invalid")
        if len(PdfReader(pdfs[0]).pages) != 1:
            raise AssertionError(f"Figure {index} PDF is not a valid single-page file")
    forbidden = [str(ROOT.parent), "/" + "Users/", ".." + "/publication", "prefabsearch" + "-web"]
    for path in list((ROOT / "code").rglob("*.py")) + [ROOT / "config/research_config.yaml"]:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text: raise AssertionError(f"non-portable dependency {token!r} in {path.relative_to(ROOT)}")


def main() -> None:
    checks = [
        ("corrected dataset and deterministic splits", check_dataset_and_splits),
        ("development-only fitting and held-out model results", check_development_fit_and_models),
        ("robustness and sensitivity outputs", check_robustness),
        ("artifact completeness and release portability", check_artifacts_and_portability),
    ]
    records = []
    for name, function in checks:
        try:
            function(); records.append({"check": name, "status": "PASS", "detail": "all assertions passed"})
            print(f"PASS: {name}")
        except Exception as error:
            records.append({"check": name, "status": "FAIL", "detail": f"{type(error).__name__}: {error}"})
            print(f"FAIL: {name}: {type(error).__name__}: {error}")
    result = {"overall_status": "PASS" if all(x["status"] == "PASS" for x in records) else "FAIL", "checks": records}
    write_json(RESULTS_DIR / "release_validation.json", result)
    lines = ["# Release Validation Report", "", f"Overall status: **{result['overall_status']}**", ""]
    lines += [f"- {row['status']}: {row['check']} - {row['detail']}" for row in records]
    lines += ["", "Validation is independent of manuscript-reported values and exits non-zero on any failed assertion.", ""]
    (RESULTS_DIR / "RELEASE_VALIDATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (RESULTS_DIR / "reproducibility_validation_report.txt").write_text(
        "\n".join(line.replace("**", "") for line in lines), encoding="utf-8"
    )
    if result["overall_status"] != "PASS": sys.exit(1)


if __name__ == "__main__":
    main()
