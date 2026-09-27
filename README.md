# PrefabSearch reproducibility release

## 1. Purpose

This is the self-contained, corrected scientific snapshot for the PrefabSearch publication. It rebuilds the site-level dataset from the included raw-coded analysis table, applies the final NSW soil special-code policy, recreates fixed splits, refits all three methods, reruns robustness analyses, regenerates figures and independently validates the outputs. It contains no web application, credentials, private configuration or dependency on the parent research repository.

## 2. Associated paper

**Geospatial decision support for prefabricated construction site screening: A reproducible comparison of weighted MCDA and machine learning**, prepared for *Results in Engineering* (Elsevier), by Maliha Tasnim and Zatul Alwani Binti Shaffiei.

The DOI is intentionally absent until archival/publication metadata exists.

## 3. Repository structure

```text
config/       locked scientific configuration
code/         preprocessing, modelling, validation and figure scripts
data/source/  release-local raw-coded analysis input and road derivative for Figure 2
data/processed/ regenerated corrected datasets
splits/       fixed main, complete-case and spatial IDs
models/       final fitted LightGBM/MLP artifacts and MLP scaler
results/      predictions, metrics, robustness outputs and audit reports
figures/      regenerated PNG and PDF figures
metadata/     provenance, dictionary, checksums and licence review
```

## 4. Python version

The final pass was executed with Python 3.13.3. Exact package versions are pinned in `requirements.txt`. Reproduction on another platform may produce tiny floating-point differences, but the split IDs, counts, thresholds and reported classifications should remain deterministic with the pinned stack.

## 5. Installation

From the release root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The complete analysis is CPU-only. LightGBM requires a working native wheel for the selected Python/platform combination.

## 6. External source datasets

PrefabSearch contains information derived from four datasets in three source families:

- **NSW Marine LiDAR Topo-Bathy 2008 Geotif:** acquired by Tenix LADS Corporation for the NSW Department of Environment and Climate Change; distributed through ELVIS under Creative Commons Attribution.
- **NSW Marine LiDAR Topo-Bathy 2011 Geotif:** acquired by Fugro Pty Ltd for the NSW Office of Environment and Heritage; distributed through ELVIS under Creative Commons Attribution.
- **NSW Road Network Categorisation:** Transport for NSW; Creative Commons Attribution 4.0 International.
- **Land and Soil Capability Mapping for NSW, Version 4.6:** NSW Department of Climate Change, Energy, the Environment and Water; Creative Commons Attribution 4.0 International.

The manifest identifies 214 Central Coast 2008 and 152 Central Coast 2011 DEM tiles, with no other elevation survey filenames. ELVIS is the distribution portal, not the data owner. The authors clipped, reprojected, resampled, sampled, cleaned, transformed and aggregated source data as detailed in the [attribution register](ATTRIBUTION.md) and [full provenance](metadata/DATA_SOURCES.md). The original providers have not endorsed the resulting analysis or conclusions.

Original government files are not included. The exact 375 filenames and SHA-256 hashes are recorded in `metadata/SOURCE_FILE_MANIFEST.csv`.

## 7. Source download instructions

The paper's reported analysis is fully reproducible from the included `data/source/analysis_grid_with_raw_lsc_codes.csv`; upstream GIS downloads are needed only to reconstruct that release input from first principles in the live research repository.

If doing so, download the exact resources through the official URLs in `metadata/DATA_SOURCES.md`, verify every checksum in `metadata/SOURCE_FILE_MANIFEST.csv`, retain the source CRS metadata and observe the documented provider terms. Do not substitute a newer catalogue export without recording its version and revalidating the scientific results.

## 8. Configuration

`config/research_config.yaml` is the single locked configuration. It defines the nine predictors, six soil-component weights, proxy thresholds, random seeds, main and spatial split rules, weighted-MCDA weights, LightGBM/MLP settings and robustness designs.

## 9. Preprocessing workflow

Run the stages individually:

```bash
python code/preprocessing/create_main_split.py
python code/preprocessing/prepare_model_dataset.py
python code/preprocessing/create_complete_case_split.py
python code/preprocessing/create_spatial_split.py
```

The special-code helper preserves ordinary LSC classes 1-8, converts code 98 (Not assessed) to missing, and marks code 99 (Water) for site exclusion. Any other out-of-domain value is missing. The ground score uses weights 0.30, 0.15, 0.15, 0.15, 0.15 and 0.10, renormalised over valid available components. Rows with no valid component receive the development-only median.

## 10. Proxy target

`prefab_label` equals 1 only when slope is below 10 degrees, Euclidean road distance is below 1,000 m and corrected ground difficulty is below 0.45. This is a **rule-derived proxy, not a completed-project outcome label and not field validation**. High model scores measure reconstruction of this rule.

## 11. Creating data splits

The main split uses `site_id`, `test_size=0.20`, `random_state=42` and stratification by the rebuilt proxy label. The resulting 16,973 development and 4,244 held-out IDs are saved under `splits/`. The complete-case cohort uses the same deterministic procedure. The directional split uses EPSG:7856 easting at 373,370 m and is an internal west-to-east sensitivity check.

## 12. Running weighted MCDA

```bash
python code/modeling/select_mcda_threshold.py
python code/modeling/run_mcda.py
```

Slope and road-distance bounds are fitted on development data only. Candidate thresholds are evaluated only on development scores, with ties resolved by maximum F1, then maximum accuracy, then the lowest threshold. The chosen threshold is 0.873051144070395. This is fixed-weight compensatory MCDA, **not full AHP**: no pairwise-comparison matrix or consistency ratio is claimed.

## 13. Running LightGBM

```bash
python code/modeling/train_gradient_boosting.py
```

The final estimator uses `class_weight="balanced"` as its only imbalance mechanism and a fixed classification threshold of 0.50. No additional sample weighting is applied. The same builder/configuration is used in the primary, CV, spatial, shuffled-label and complete-case runs.

## 14. Running MLP

```bash
python code/modeling/train_mlp.py
```

The `StandardScaler` is fitted on development rows only. Early stopping takes its internal validation fraction only from those development rows. The held-out set is transformed with the frozen scaler and touched only for final evaluation.

## 15. Running robustness analyses

```bash
python code/validation/complete_case_soil_sensitivity.py
python code/validation/run_lightgbm_robustness.py
python code/validation/mcda_weight_sensitivity.py
python code/validation/permutation_importance.py
```

These recreate the strict six-field complete-case sensitivity, five-fold stratified CV confined to the main development set, west-to-east internal check, fixed-feature shuffled-label negative control, 5,000 MCDA weight perturbations at +/-20%, boundary-window analysis and held-out F1 permutation importance with 20 repeats. Permutation importance is predictive sensitivity, not causal importance.

## 16. Recreating figures

```bash
MPLBACKEND=Agg python code/figures/generate_figures.py
```

Six matching PNG/PDF pairs are written to `figures/`. Figure 2 uses the included EPSG:7856 road derivative and study boundary; its easting labels are formatted in kilometres to avoid overlap.

## 17. Running validation

```bash
python code/validation/validate_release_results.py
```

The validator independently rebuilds the corrected table/splits, checks development-only preprocessing, loads model artifacts, reproduces probabilities and every metric, reruns MCDA sensitivity and permutation calculations, verifies robustness prediction tables and boundary analysis, checks figure files and scans for parent-repository dependencies. Any critical failure exits non-zero and writes `results/release_validation.json` plus `results/reproducibility_validation_report.txt`.

For a full rebuild followed by validation:

```bash
python code/run_full_rebuild.py
```

## 18. Expected final verified values

- Final dataset: 21,217 sites; 18,822 proxy-negative and 2,395 proxy-positive (11.288%).
- Main split: 16,973 development; 4,244 held out.
- Soil: 18,030 fully missing (84.979%); 3,187 valid-soil and strict complete-case rows; 81 code-98 rows retained as missing; 9 code-99 Water rows excluded.
- Weighted MCDA held out: accuracy 0.9423, precision 0.7882, recall 0.6681, F1 0.7232, ROC-AUC 0.9275, AP 0.7911; confusion matrix [[3679, 86], [159, 320]].
- LightGBM held out: accuracy 0.9988, precision 0.9958, recall 0.9937, F1 0.9948, ROC-AUC 0.99998, AP 0.99987; confusion matrix [[3763, 2], [3, 476]].
- MLP held out: accuracy 0.9958, precision 0.9832, recall 0.9791, F1 0.9812, ROC-AUC 0.99986, AP 0.99896; confusion matrix [[3757, 8], [10, 469]].
- Development-only LightGBM five-fold CV: F1 0.99530 +/- 0.00411; ROC-AUC 0.99997 +/- 0.00003; AP 0.99976 +/- 0.00024.
- West-to-east LightGBM: F1 0.99230, ROC-AUC 0.99995, AP 0.99965.
- Shuffled-label control: F1 0.17820, ROC-AUC 0.49293, AP 0.11788.
- MCDA sensitivity: median Spearman 0.99836 (5th-95th 0.99110-0.99980), median 132 changed classifications (22-325), median 404 positives (155-729.05), median F1 0.68541 (0.46606-0.75109).

Machine-readable values, including unrounded numbers, are authoritative.

## 19. Known limitations

- The target is deterministic and partly constructed from the same predictors used by the models, so performance is proxy reconstruction rather than independent outcome prediction.
- Soil coverage is sparse: 84.979% of retained sites have no valid mapped evidence in the six selected fields; the 3,187-row complete-case check does not provide external validation.
- Land and Soil Capability mapping was developed for land-capability purposes, not parcel-scale geotechnical design.
- `road_distance_m` is Euclidean proximity to the acquired categorised network, an early-screening approximation rather than route distance, haulage feasibility or legal access.
- The spatial split is directional and internal. It is not temporal, jurisdictional or completed-project validation.
- Fixed-weight MCDA is compensatory and is not full AHP.
- Planning, ownership, utilities, detailed geotechnical conditions, flooding, module transport constraints, crane access and approvals are outside scope.

## 20. Licensing

Author-owned code, configuration and associated software/model artifacts are covered by the repository's [MIT licence](LICENSE). Third-party-derived data remain subject to their respective source licences and attribution requirements. See the [attribution register](ATTRIBUTION.md), [full provenance](metadata/DATA_SOURCES.md), [detailed licensing boundaries](metadata/LICENSE_NOTES.md) and [derived-data review](metadata/DERIVED_DATA_LICENSE_REVIEW.md).

The restricted Tenix/Fugro survey reports are not included or relicensed. Original author-created documentation and figures are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/), approved by the author on 2026-09-28; applicable source attribution requirements also remain in force.

## 21. Citation

Use `CITATION.cff`. It includes only author names verified from the associated manuscript and deliberately omits DOI/ORCID values that do not yet exist in the release metadata. Add the Zenodo DOI only after deposit.
