# External data sources and release-local derivatives

The release uses four datasets in three government source families: elevation, roads, and land and soil capability. The [source manifest](SOURCE_FILE_MANIFEST.csv) lists 375 exact source filenames and SHA-256 hashes. Review on 2026-09-28 found 214 `CentralCoast2008-DEM-AHD-5m_*.tif` tiles and 152 `CentralCoast2011-DEM-AHD-5m_*.tif` tiles: all 366 DEM filenames match the two verified surveys. No filename indicates another elevation survey. The remaining inputs are one road JSON and eight soil shapefile components. This is a filename-to-source reconciliation using the supplied verified provenance, not a fresh inspection of the original rasters.

Original download/access dates were not consistently recorded and are not inferred from file timestamps. Licensing, provider attribution and redistribution conditions were verified using the cited official catalogue records and the retained source metadata reviewed for this release.

ELVIS is the elevation distribution portal, not necessarily the original data creator. Source attribution and modification notices are also collected in [ATTRIBUTION.md](../ATTRIBUTION.md).

## 1. NSW Marine LiDAR Topo-Bathy 2008 GeoTIFF

- Exact catalogue title: `NSW Marine LiDAR Topo-Bathy 2008 Geotif` (GeoTIFF format).
- Commissioning agency: NSW Department of Environment and Climate Change; data acquisition by Tenix LADS Corporation.
- Acquisition period: March 2008; survey coverage: NSW Central and Hunter coasts.
- Official dataset URL: [NSW catalogue record](https://www.data.nsw.gov.au/data/dataset/marine-lidar-topo-bathy-2008).
- Distributor: [ELVIS Elevation and Depth portal](https://elevation.fsdf.org.au/).
- Exact inputs: 214 `CentralCoast2008-DEM-AHD-5m_*.tif` files in the manifest; Australian Height Datum, 5 m grid, 1 km tiles.
- Source CRS: GDA94 / MGA zone 56 (EPSG:28356).
- Licence: Creative Commons Attribution, as identified by the official NSW catalogue; no specific version is asserted.
- Licence URL/evidence: [official dataset licence field](https://www.data.nsw.gov.au/data/dataset/marine-lidar-topo-bathy-2008). A version-specific licence URL is not assigned without authoritative version evidence.
- Access date: original download date not recorded; retained files were present locally by 2026-04-26.
- Purpose in PrefabSearch: valid-elevation footprint, 5 m elevation, slope and study-area boundary derivation.
- Author transformations: Source elevation data were clipped, resampled, spatially processed and used to derive terrain variables for this study.
- Required attribution: Contains information derived from NSW Marine LiDAR Topo-Bathy 2008 Geotif, acquired by Tenix LADS Corporation for the NSW Department of Environment and Climate Change and distributed through ELVIS under a Creative Commons Attribution licence.
- Non-endorsement: NSW Department of Environment and Climate Change and Tenix LADS Corporation have not endorsed the resulting analysis or conclusions.
- Redistribution status: VERIFIED — redistribution permitted with attribution. Original raster files are not included; source-derived release data retain source attribution requirements. To reconstruct upstream GIS features, place original tiles in `data/raw/elevation/` in the live research repository, not this snapshot.

## 2. NSW Marine LiDAR Topo-Bathy 2011 GeoTIFF

- Exact catalogue title: `NSW Marine LiDAR Topo-Bathy 2011 Geotif` (GeoTIFF format).
- Commissioning agency: NSW Office of Environment and Heritage; data acquisition by Fugro Pty Ltd.
- Acquisition period: June–July 2011; survey coverage: Central Coast, Port Stephens, Byron Bay and Tweed Heads.
- Official dataset URL: [NSW catalogue record](https://data.nsw.gov.au/data/dataset/marine-lidar-topo-bathy-2011).
- Distributor: [ELVIS Elevation and Depth portal](https://elevation.fsdf.org.au/).
- Exact inputs: 152 `CentralCoast2011-DEM-AHD-5m_*.tif` files in the manifest; Australian Height Datum, 5 m grid, 1 km tiles.
- Source CRS: GDA94 / MGA zone 56 (EPSG:28356).
- Licence: Creative Commons Attribution, as identified by the official NSW catalogue; no specific version is asserted.
- Licence URL/evidence: [official dataset licence field](https://data.nsw.gov.au/data/dataset/marine-lidar-topo-bathy-2011). A version-specific licence URL is not assigned without authoritative version evidence.
- Access date: original download date not recorded; retained files were present locally by 2026-04-26.
- Purpose in PrefabSearch: valid-elevation footprint, 5 m elevation, slope and study-area boundary derivation.
- Author transformations: Source elevation data were clipped, resampled, spatially processed and used to derive terrain variables for this study.
- Required attribution: Contains information derived from NSW Marine LiDAR Topo-Bathy 2011 Geotif, acquired by Fugro Pty Ltd for the NSW Office of Environment and Heritage and distributed through ELVIS under a Creative Commons Attribution licence.
- Non-endorsement: NSW Office of Environment and Heritage and Fugro Pty Ltd have not endorsed the resulting analysis or conclusions.
- Redistribution status: VERIFIED — redistribution permitted with attribution. Original raster files are not included; source-derived release data retain source attribution requirements. To reconstruct upstream GIS features, place original tiles in `data/raw/elevation/` in the live research repository, not this snapshot.

## 3. NSW Road Network Categorisation

- Exact dataset title: `NSW Road Network Categorisation`.
- Provider: Transport for NSW.
- Acquisition year: not recorded; a local file timestamp of 2026-04-20 is not an acquisition or download date.
- Official dataset URL/distributor: [Transport for NSW Open Data Hub](https://opendata.transport.nsw.gov.au/data/dataset/nsw-roads-network-categorisation).
- Licence: Creative Commons Attribution 4.0 International; [licence URL](https://creativecommons.org/licenses/by/4.0/).
- Access date: original download date not recorded.
- Exact input: `nsw_road_network_categorisation.json`, SHA-256 `8e21c664c8fcb9fc07ea8daef2d012ed354bd4b44a1306f90002e29e73afd6e8`.
- Source CRS: WGS 84 / Pseudo-Mercator (EPSG:3857), as recorded in the source JSON CRS.
- Purpose in PrefabSearch: Euclidean distance from each analysis point to the acquired State/Regional road layer.
- Author transformations: The road data were reprojected, clipped and processed to calculate Euclidean proximity to the acquired categorised road network.
- Required attribution and non-endorsement: Contains information derived from the NSW Road Network Categorisation dataset, Transport for NSW, licensed under the Creative Commons Attribution 4.0 International Licence. The source data were reprojected, clipped and processed for this study. Transport for NSW has not endorsed the resulting analysis or conclusions.
- Redistribution status: VERIFIED — redistribution permitted with attribution. Original JSON is not included. The release-local derivative `data/source/roads_7856.gpkg`, clipped/reprojected to EPSG:7856, is included to regenerate Figure 2; SHA-256 `1ae4e867c77b65b3d91982d2a70f41edc30dcbc17b7646906348da49e907f542`.

## 4. Land and Soil Capability Mapping for NSW, Version 4.6

- Exact dataset title: `Land and Soil Capability Mapping for NSW`; edition: 4.6.
- Provider/custodian: NSW Department of Climate Change, Energy, the Environment and Water.
- Acquisition year: not recorded; edition 4.6 identifies the source version, not a verified acquisition date.
- Dataset identifier: `4BC12CBF-F119-4788-8C5A-A86466EC6412`.
- Official dataset URI: [NSW Information Asset Register](https://iar.environment.nsw.gov.au/dataset/4BC12CBF-F119-4788-8C5A-A86466EC6412).
- Distributor: NSW SEED portal; [catalogue record](https://datasets.seed.nsw.gov.au/dataset/land-and-soil-capability-mapping-for-nsw4bc12).
- Licence: Creative Commons Attribution 4.0 International; [licence URL](https://creativecommons.org/licenses/by/4.0/).
- Access date: original download date not recorded.
- Exact inputs: eight components of `LSC_MstLmtAll_NSW_v4_6_251010.*`, listed in the manifest.
- Source CRS: GDA94 geographic coordinates (EPSG:4283).
- Purpose in PrefabSearch: six mapped limitation attributes and the corrected ground-difficulty composite.
- Fields used: `LSC_MstLmt`, `LSC_WatrEr`, `LSC_Watlog`, `LSC_Mass_m`, `LSC_Sh_Rk`, `LSC_StrD`; descriptive fields `LSCMstLmtN` and `LimitnHazN` are retained for audit only.
- Author transformations: The source polygons and Land and Soil Capability attributes were spatially sampled, cleaned, transformed and aggregated for this study. Special values 98 and 99 were handled according to the documented release policy.
- Required attribution and non-endorsement: Contains information derived from Land and Soil Capability Mapping for NSW, Version 4.6, NSW Department of Climate Change, Energy, the Environment and Water, licensed under the Creative Commons Attribution 4.0 International Licence. The source data were spatially sampled, cleaned, transformed and aggregated for this study. The department has not endorsed the resulting analysis or conclusions.
- Redistribution status: VERIFIED — redistribution permitted with attribution. Original shapefile components are not included; point-sampled and processed derivatives retain source attribution requirements.

## Excluded supporting survey reports

`CentralCoast2008_metadata.pdf` (Tenix) and `CentralCoast2011_metadata.pdf` (Fugro) contain restrictive copyright and confidentiality wording. They are not part of the public release, are not covered by the datasets' Creative Commons licences, and are not relicensed here. Neither file was found anywhere in this repository during the 2026-09-28 inspection. They must not be included in GitHub or Zenodo.

## Release-local analysis source and boundary

`data/source/analysis_grid_with_raw_lsc_codes.csv` is the release-local scientific starting table (SHA-256 `74f4fc79f019f24e0e994f480a3857feb15168680cd0d37e3a8f088e40ff0910`). It contains site-level terrain, road distance and uncorrected/raw mapped LSC codes, including 98 and 99, plus explicitly named `legacy_*` fields used only for the before/after audit. Those legacy fields are never model predictors.

`data/study_area_boundary.geojson` is the exact DEM-validity-derived study boundary in EPSG:4326 (SHA-256 `4e5cdfa421940e2285f6204037dada900e4ea25ad5715ee261b22eb27b646f68`). It is a research-derived availability footprint, not an administrative boundary.

These derivatives are verified for redistribution with applicable source attribution; see the [derived-data review](DERIVED_DATA_LICENSE_REVIEW.md) and [licensing boundaries](LICENSE_NOTES.md). This release documentation is not legal advice.
