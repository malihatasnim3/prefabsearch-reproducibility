# Derived-data licence review


| Artifact category | Release paths | Source relationship |
|---|---|---|---|
| Raw-coded analysis table | `data/source/analysis_grid_with_raw_lsc_codes.csv` | Point samples and derivatives of elevation, roads and NSW LSC mapping |
| Corrected processed tables | `data/processed/*.csv` | Transformations and imputations derived from the source table |
| Reprojected/clipped road geometry | `data/source/roads_7856.gpkg` | Derived from Transport for NSW road data |
| Study-area boundary | `data/study_area_boundary.geojson` | Polygonised/simplified valid DEM coverage |
| Fixed split identifiers | `splits/*.csv` | Subsets/orderings of derived `site_id` values |
| Trained model binaries | `models/*.joblib` | Parameters fitted from derived feature data |
| Site-level predictions/components | `results/model_predictions/*.csv`, `results/*predictions.csv` | Model/MCDA outputs linked to derived site identifiers |
| Aggregate result tables/reports | `results/*.json`, remaining `results/*.csv`, `results/*.md`, `results/*.txt` | Author-generated summaries of derived data |
| Figures | `figures/*.png`, `figures/*.pdf` | Author-generated visualisations of derived information |
| Source-code and methodological prose | `code/**/*.py`, `config/research_config.yaml`, root/metadata Markdown written by the authors | Author-owned expression |

Before archiving, a human reviewer should (1) inspect exact ELVIS order metadata, (2) confirm Transport for NSW attribution requirements, (3) confirm NSW DCCEEW CC BY 4.0 attribution text, (4) decide whether site-level derivatives and model binaries may be redistributed, and (5) record the chosen non-code/documentation licence. Do not infer that the root MIT licence resolves these questions.
