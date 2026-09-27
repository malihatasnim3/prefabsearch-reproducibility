# READY FOR ZENODO

The reproducibility snapshot is scientifically and technically complete. A full rebuild from a copy containing only this release succeeded in `/tmp`, and the independent validator passed all four critical groups: corrected dataset and deterministic splits; development-only fitting and held-out results; robustness and sensitivity outputs; and artifact completeness and portability.

The archive is ready to be prepared for Zenodo after the human-review items below are resolved. No upload, DOI registration, GitHub release, or journal submission was performed.

# NEEDS HUMAN REVIEW

- Replace the manuscript's `[INSERT ARCHIVED RESEARCH ARTIFACT DOI/URL]` placeholder and add the issued DOI to `CITATION.cff` only after a Zenodo record exists.
- Authors should perform a final editorial read and confirm author, affiliation, funding, competing-interest, CRediT, AI-use, and acknowledgement statements before submission.

# BLOCKERS

There are no scientific, computational, validation, or portability blockers. The three underlying source families (elevation, roads, and land and soil capability) have been licence-verified using the supplied verified evidence. All 366 DEM filenames match the verified 2008/2011 surveys (214/152); no additional elevation source appears. Attribution and modification notices have been added in [ATTRIBUTION.md](ATTRIBUTION.md) and [DATA_SOURCES.md](metadata/DATA_SOURCES.md). The restricted Tenix/Fugro supporting survey reports are absent and excluded from GitHub and Zenodo.

Source licensing is no longer an unresolved Zenodo blocker. The author approved CC BY 4.0 for original author-created documentation and figures on 2026-09-28. The repository is ready for public GitHub release and Zenodo deposit from a licensing-documentation perspective; see [licensing boundaries](metadata/LICENSE_NOTES.md). DOI metadata, author statements and editorial review remain pending as listed; no release or deposit is claimed. This update changed licensing/provenance documentation only and did not rerun experiments or alter scientific artifacts or reported results.

# FINAL VERIFIED NUMBERS

- **Dataset:** 21,217 final observations from 21,554 candidates; 103 invalid-elevation exclusions, 225 other terrain/accessibility exclusions, and 9 code-99 Water exclusions. The final class counts are 18,822 proxy-negative and 2,395 proxy-positive (11.288118% positive). Sixteen retained labels changed after the soil-code correction.
- **Main split:** 16,973 development observations and 4,244 held-out observations, using `site_id`, 20% test size, random seed 42, and stratification. The held-out set contains 3,765 negatives and 479 positives.
- **Soil evidence:** 81 code-98 rows were retained as missing; 9 code-99 rows were excluded; 18,030 final rows have no valid six-field soil evidence (84.979026%); 3,187 rows have valid ordinary values in all six LSC fields and form the strict complete-case cohort. The development-fitted ground-score median is 0.3214285714.
- **Weighted MCDA, held out:** threshold 0.8730511441; accuracy 0.942271, precision 0.788177, recall 0.668058, F1 0.723164, ROC-AUC 0.927498, AP 0.791138; confusion matrix `[[3679, 86], [159, 320]]`.
- **LightGBM, held out:** accuracy 0.998822, precision 0.995816, recall 0.993737, F1 0.994775, ROC-AUC 0.999984, AP 0.999867; confusion matrix `[[3763, 2], [3, 476]]`. Class imbalance is handled once through `class_weight="balanced"`.
- **MLP, held out:** accuracy 0.995759, precision 0.983229, recall 0.979123, F1 0.981172, ROC-AUC 0.999860, AP 0.998956; confusion matrix `[[3757, 8], [10, 469]]`.
- **Complete-case sensitivity:** 2,549 development and 638 test observations, with 200 positive test observations (31.35%). F1 is 0.792746 for weighted MCDA, 0.992556 for LightGBM, and 0.992519 for MLP.
- **Development-only five-fold LightGBM CV:** accuracy 0.998940 +/- 0.000924, precision 0.995323 +/- 0.004729, recall 0.995304 +/- 0.006264, F1 0.995299 +/- 0.004106, ROC-AUC 0.999968 +/- 0.000031, and AP 0.999756 +/- 0.000235.
- **West-to-east sensitivity:** 10,639 western development observations and 10,578 eastern test observations; accuracy 0.998109, precision 0.987730, recall 0.996904, F1 0.992296, ROC-AUC 0.999953, AP 0.999654; confusion matrix `[[9270, 16], [4, 1288]]`. This is an internal directional check, not external validation.
- **Shuffled-label control:** accuracy 0.591423, precision 0.115408, recall 0.390852, F1 0.178199, ROC-AUC 0.492931, and AP 0.117881.
- **MCDA weight sensitivity, 5,000 +/-20% scenarios:** median Spearman correlation 0.998359 (5th–95th percentiles 0.991095–0.999799); median 132 changed classifications (22–325); median 404 positive predictions (155–729.05); median F1 0.685408 (0.466057–0.751088).

All performance values measure agreement with a deterministic rule-derived proxy. They are not field validation or evidence of completed-project construction suitability.
