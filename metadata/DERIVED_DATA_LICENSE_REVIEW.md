# Derived-data licence review

Reviewed on 2026-09-28 against the supplied verified source evidence and [source manifest](SOURCE_FILE_MANIFEST.csv). All 366 DEM filenames match Central Coast 2008 (214) or Central Coast 2011 (152); no other elevation source appears. The road input and eight soil components match the other two verified source families. [Full provenance](DATA_SOURCES.md) records the evidence and transformations.

| Artifact category | Release paths | Source relationship | Current status |
|---|---|---|---|
| Raw-coded analysis table | `data/source/analysis_grid_with_raw_lsc_codes.csv` | Point samples and derivatives of elevation, roads and NSW LSC mapping | VERIFIED — redistribution permitted with attribution |
| Corrected processed tables | `data/processed/*.csv` | Transformations and imputations derived from the source table | VERIFIED — redistribution permitted with attribution |
| Reprojected/clipped road geometry | `data/source/roads_7856.gpkg` | Transport for NSW road derivative | VERIFIED — redistribution permitted with attribution |
| Study-area boundary | `data/study_area_boundary.geojson` | Polygonised/simplified valid DEM coverage | VERIFIED — redistribution permitted with attribution |
| Fixed split identifiers | `splits/*.csv` | Subsets/orderings of derived `site_id` values | VERIFIED — redistribution permitted with attribution |
| Trained model binaries | `models/*.joblib` | Author-generated fitted parameters and scaler | AUTHOR-GENERATED — distribution permitted under MIT |
| Site-level predictions/components | `results/model_predictions/*.csv`, `results/*predictions.csv` | Model/MCDA outputs linked to derived site identifiers | VERIFIED — redistribution permitted with attribution |
| Aggregate result tables/reports | `results/*.json`, remaining `results/*.csv`, `results/*.md`, `results/*.txt` | Author-generated summaries of derived data | VERIFIED — redistribution permitted with attribution |
| Figures | `figures/*.png`, `figures/*.pdf` | Author-generated visualisations of derived information | VERIFIED — redistribution permitted with attribution; CC BY 4.0 for original author expression |
| Source code, configuration and associated software artifacts | `code/**/*.py`, `config/research_config.yaml`, `models/*.joblib` | Author-owned software | AUTHOR-GENERATED — distribution permitted under MIT |
| Original author-created documentation | Root/metadata Markdown and report prose | Author-owned expression | AUTHOR-GENERATED — distribution permitted under CC BY 4.0; see LICENSE_NOTES.md |
| Tenix/Fugro supporting reports | `CentralCoast2008_metadata.pdf`, `CentralCoast2011_metadata.pdf` (absent) | Restrictive third-party supporting documents | NOT INCLUDED — restrictive supporting report |

Source-derived data remain subject to the applicable source attribution requirements: Creative Commons Attribution for the NSW Marine LiDAR 2008/2011 datasets (version not asserted), and CC BY 4.0 for Transport for NSW roads and NSW Land and Soil Capability v4.6. Preserve the [attribution register](../ATTRIBUTION.md) and documented modification notices. The repository does not relicense third-party source material under MIT.

Trained model binaries are author-generated computational artifacts. They contain fitted parameters and preprocessing state, not the original government raster/vector files, and are distributed under MIT as part of the reproducibility software release. This determination and the source review are release documentation, not legal advice.

The original Tenix/Fugro reports are excluded. No unverified source or source-licensing manual-review warning remains. The author explicitly approved CC BY 4.0 for original author-created documentation and figures on 2026-09-28. Source attribution requirements remain applicable in addition to that licence.
