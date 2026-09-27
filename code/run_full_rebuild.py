#!/usr/bin/env python3
"""Run the complete corrected analysis, figures, and independent validation."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [
    "code/preprocessing/create_main_split.py",
    "code/preprocessing/prepare_model_dataset.py",
    "code/preprocessing/create_complete_case_split.py",
    "code/preprocessing/create_spatial_split.py",
    "code/modeling/run_all_models.py",
    "code/validation/build_held_out_predictions.py",
    "code/validation/evaluate_models.py",
    "code/validation/complete_case_soil_sensitivity.py",
    "code/validation/run_lightgbm_robustness.py",
    "code/validation/mcda_weight_sensitivity.py",
    "code/validation/permutation_importance.py",
    "code/figures/generate_figures.py",
    "code/validation/validate_release_results.py",
]


def main() -> None:
    environment = os.environ.copy()
    cache_root = Path(tempfile.gettempdir()) / "prefabsearch_reproducibility_cache"
    environment.update({
        "MPLBACKEND": "Agg",
        "MPLCONFIGDIR": str(cache_root / "matplotlib"),
        "XDG_CACHE_HOME": str(cache_root),
        "LOKY_MAX_CPU_COUNT": "1",
        "PYTHONHASHSEED": "0",
    })
    for step in STEPS:
        print(f"\n=== {step} ===", flush=True)
        subprocess.run([sys.executable, step], cwd=ROOT, env=environment, check=True)
    print("\nFull rebuild and validation completed successfully.")


if __name__ == "__main__":
    main()
