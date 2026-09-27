"""Run all final model fits and build the site-ID-aligned held-out table."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STEPS = [
    ROOT / "code/modeling/select_mcda_threshold.py",
    ROOT / "code/modeling/run_mcda.py",
    ROOT / "code/modeling/train_gradient_boosting.py",
    ROOT / "code/modeling/train_mlp.py",
    ROOT / "code/validation/build_held_out_predictions.py",
    ROOT / "code/validation/evaluate_models.py",
]

if __name__ == "__main__":
    for step in STEPS:
        print(f"[modeling] {step.name}", flush=True)
        subprocess.run([sys.executable, str(step)], cwd=ROOT, check=True)
