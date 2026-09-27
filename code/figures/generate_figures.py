#!/usr/bin/env python3
"""Regenerate all six publication/reproducibility figures from release-local data."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/prefabsearch_release_mpl")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/prefabsearch_release_cache")

import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter, MaxNLocator
from shapely import wkt

RELEASE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RELEASE_ROOT / "code"))

from common import ensure_directories  # noqa: E402

FIGURE_DIR = RELEASE_ROOT / "figures"
COLORS = {
    "navy": "#183153",
    "blue": "#2F6B9A",
    "teal": "#2A9D8F",
    "gold": "#E9C46A",
    "orange": "#F4A261",
    "red": "#C8553D",
    "grey": "#5F6B76",
    "light": "#EFF4F8",
}


def save(fig: plt.Figure, stem: str) -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURE_DIR / f"{stem}.png", dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURE_DIR / f"{stem}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def figure_1() -> None:
    fig, ax = plt.subplots(figsize=(13.5, 6.5))
    ax.set_xlim(0, 13.5)
    ax.set_ylim(0, 7)
    ax.axis("off")
    boxes = [
        (0.25, 4.25, 2.8, 1.4, "Source evidence", "Terrain, roads and raw LSC codes"),
        (3.55, 4.25, 2.8, 1.4, "Scientific correction", "99 excluded as water\n98 retained as missing"),
        (6.85, 4.25, 2.8, 1.4, "Deterministic target", "Slope, road access and\nsoil-difficulty proxy"),
        (10.15, 4.25, 2.8, 1.4, "Fixed main split", "16,973 development\n4,244 held out"),
        (1.0, 1.25, 3.0, 1.4, "Weighted MCDA", "Fixed weights; development-only\nnormalisation and threshold"),
        (5.25, 1.25, 3.0, 1.4, "LightGBM", "Single balanced-class mechanism\nfixed probability threshold"),
        (9.5, 1.25, 3.0, 1.4, "MLP", "Development-fitted scaler\nand internal early stopping"),
    ]
    for i, (x, y, w, h, title, body) in enumerate(boxes):
        fc = COLORS["light"] if i < 4 else "#FDF7E8"
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.08",
                               facecolor=fc, edgecolor=COLORS["navy"], linewidth=1.3)
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h * 0.68, title, ha="center", va="center",
                fontsize=10.5, fontweight="bold", color=COLORS["navy"])
        ax.text(x + w / 2, y + h * 0.32, body, ha="center", va="center", fontsize=8.8,
                color=COLORS["grey"], linespacing=1.3)
    for x1, x2 in [(3.05, 3.55), (6.35, 6.85), (9.65, 10.15)]:
        ax.add_patch(FancyArrowPatch((x1, 4.95), (x2, 4.95), arrowstyle="-|>",
                                     mutation_scale=13, color=COLORS["blue"], linewidth=1.4))
    for x in (2.5, 6.75, 11.0):
        ax.add_patch(FancyArrowPatch((11.55, 4.25), (x, 2.65), arrowstyle="-|>",
                                     connectionstyle="arc3,rad=0.05", mutation_scale=13,
                                     color=COLORS["blue"], linewidth=1.2))
    ax.text(6.75, 6.45, "Reproducible prefab-suitability modelling framework", ha="center",
            va="center", fontsize=16, fontweight="bold", color=COLORS["navy"])
    ax.text(6.75, 0.45, "All reported metrics are internal agreement with the deterministic proxy target, not field validation.",
            ha="center", va="center", fontsize=9.5, color=COLORS["red"])
    save(fig, "Figure_1_reproducible_framework")


def figure_2() -> None:
    sites = pd.read_csv(RELEASE_ROOT / "data/processed/site_features.csv")
    sites["geometry"] = sites["geometry"].map(wkt.loads)
    sites = gpd.GeoDataFrame(sites, geometry="geometry", crs="EPSG:7856")
    boundary = gpd.read_file(RELEASE_ROOT / "data/study_area_boundary.geojson").to_crs("EPSG:7856")
    roads = gpd.read_file(RELEASE_ROOT / "data/source/roads_7856.gpkg").to_crs("EPSG:7856")

    fig, ax = plt.subplots(figsize=(11.5, 8.2))
    boundary.plot(ax=ax, facecolor="#F8F5EB", edgecolor=COLORS["navy"], linewidth=1.1, zorder=1)
    roads.plot(ax=ax, color="#9DA8B2", linewidth=0.45, alpha=0.7, zorder=2)
    sample = sites.iloc[::3].copy()
    sample.plot(ax=ax, column="prefab_label", categorical=True,
                cmap="RdYlGn", markersize=3.0, alpha=0.62, zorder=3)
    xmin, ymin, xmax, ymax = boundary.total_bounds
    pad_x, pad_y = (xmax - xmin) * 0.025, (ymax - ymin) * 0.025
    ax.set_xlim(xmin - pad_x, xmax + pad_x)
    ax.set_ylim(ymin - pad_y, ymax + pad_y)
    ax.set_aspect("equal")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=6))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=7))
    thousands = FuncFormatter(lambda value, _pos: f"{value / 1000:,.0f}")
    ax.xaxis.set_major_formatter(thousands)
    ax.yaxis.set_major_formatter(thousands)
    ax.tick_params(axis="x", labelrotation=25, labelsize=9)
    ax.tick_params(axis="y", labelsize=9)
    ax.set_xlabel("Easting (km), MGA Zone 56 / EPSG:7856")
    ax.set_ylabel("Northing (km), MGA Zone 56 / EPSG:7856")
    ax.set_title("Study area, road network and corrected analysis-grid labels", fontsize=14,
                 fontweight="bold", color=COLORS["navy"], pad=12)
    handles = [
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#A50026", alpha=.75,
                   markersize=7, label="Proxy label 0"),
        plt.Line2D([0], [0], marker="o", color="none", markerfacecolor="#006837", alpha=.75,
                   markersize=7, label="Proxy label 1"),
        plt.Line2D([0], [0], color="#9DA8B2", lw=1.5, label="Road network"),
    ]
    ax.legend(handles=handles, loc="upper left", frameon=True, framealpha=.95, fontsize=9)
    ax.text(0.01, 0.012, "Every third site is displayed for legibility.\nAll 21,217 retained sites are analysed.",
            transform=ax.transAxes, fontsize=8.5, color=COLORS["grey"],
            bbox=dict(facecolor="white", alpha=.85, edgecolor="none", pad=3))
    fig.tight_layout()
    save(fig, "Figure_2_study_area_map")


def figure_3() -> None:
    df = pd.read_csv(RELEASE_ROOT / "results/held_out_metrics.csv")
    labels = {"weighted_mcda": "Weighted MCDA", "gradient_boosting": "LightGBM", "mlp": "MLP"}
    metrics = ["accuracy", "precision", "recall", "f1", "roc_auc", "average_precision"]
    shown = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC", "Avg. precision"]
    x = np.arange(len(metrics)); width = 0.23
    fig, ax = plt.subplots(figsize=(10.8, 5.8))
    for i, (name, row) in enumerate(df.set_index("method").iterrows()):
        ax.bar(x + (i - 1) * width, [row[m] for m in metrics], width,
               label=labels[name], color=[COLORS["blue"], COLORS["teal"], COLORS["orange"]][i])
    ax.set_ylim(0.6, 1.02)
    ax.set_xticks(x, shown)
    ax.set_ylabel("Held-out score")
    ax.set_title("Corrected held-out performance (n = 4,244)", fontsize=14,
                 fontweight="bold", color=COLORS["navy"], pad=24)
    ax.grid(axis="y", alpha=.22)
    ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(.5, -0.19), frameon=False)
    ax.text(.5, 1.01, "Proxy-target agreement; not field validation", ha="center", va="bottom",
            transform=ax.transAxes, fontsize=8.5, color=COLORS["red"])
    fig.tight_layout()
    save(fig, "Figure_3_held_out_performance")


def figure_4() -> None:
    with open(RELEASE_ROOT / "results/verified_metrics.json", encoding="utf-8") as f:
        held = json.load(f)["held_out"]
    entries = [("Weighted MCDA", held["weighted_mcda"]),
               ("LightGBM", held["gradient_boosting"]), ("MLP", held["mlp"])]
    fig, axes = plt.subplots(1, 3, figsize=(12.8, 4.5), constrained_layout=True)
    for ax, (name, result) in zip(axes, entries):
        cm = np.array(result["confusion_matrix"])
        im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=max(np.array(x[1]["confusion_matrix"]).max() for x in entries))
        for (i, j), value in np.ndenumerate(cm):
            ax.text(j, i, f"{value:,}", ha="center", va="center", fontweight="bold",
                    color="white" if value > cm.max() * .55 else COLORS["navy"], fontsize=12)
        ax.set_xticks([0, 1], ["Predicted 0", "Predicted 1"])
        ax.set_yticks([0, 1], ["Actual 0", "Actual 1"])
        ax.set_title(f"{name}\nF1 = {result['f1']:.3f}", fontsize=12, fontweight="bold")
    fig.suptitle("Held-out confusion matrices after scientific correction", fontsize=14,
                 fontweight="bold", color=COLORS["navy"])
    save(fig, "Figure_4_confusion_matrices")


def figure_5() -> None:
    df = pd.read_csv(RELEASE_ROOT / "results/permutation_importance.csv")
    label_map = {
        "road_distance_m": "Road distance", "ground_difficulty_score": "Ground difficulty",
        "LSC_MstLmt": "Moisture limitation", "LSC_WatrEr": "Water erosion",
        "LSC_Watlog": "Waterlogging", "LSC_Mass_m": "Mass movement",
        "LSC_Sh_Rk": "Shallow rock", "LSC_StrD": "Structural decline", "slope": "Slope",
    }
    order = (df.groupby("feature")["importance_mean"].max().sort_values()).index
    y = np.arange(len(order)); height = .35
    fig, ax = plt.subplots(figsize=(10.2, 6.2))
    for i, (method, color) in enumerate([("LightGBM", COLORS["teal"]), ("MLP", COLORS["orange"])]):
        part = df[df.method == method].set_index("feature").loc[order]
        ax.barh(y + (i - .5) * height, part.importance_mean, height,
                xerr=part.importance_std, capsize=2, label=method, color=color, alpha=.92)
    ax.set_yticks(y, [label_map[x] for x in order])
    ax.axvline(0, color=COLORS["grey"], linewidth=.8)
    ax.set_xlabel("Decrease in held-out F1 after feature permutation")
    ax.set_title("Held-out permutation importance (20 repeats)", fontsize=14,
                 fontweight="bold", color=COLORS["navy"])
    ax.grid(axis="x", alpha=.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    save(fig, "Figure_5_permutation_importance")


def figure_6() -> None:
    df = pd.read_csv(RELEASE_ROOT / "results/gradient_boosting_robustness.csv")
    df = df[df.evaluation != "Development five-fold CV (std)"].copy()
    labels = ["Random\nheld-out", "Development\n5-fold CV", "West-to-east\nsplit", "Shuffled-label\ncontrol"]
    metrics = ["accuracy", "f1", "roc_auc", "average_precision"]
    shown = ["Accuracy", "F1", "ROC-AUC", "Avg. precision"]
    x = np.arange(len(df)); width = .18
    fig, ax = plt.subplots(figsize=(10.6, 5.8))
    for i, (metric, name) in enumerate(zip(metrics, shown)):
        ax.bar(x + (i - 1.5) * width, df[metric], width, label=name,
               color=[COLORS["blue"], COLORS["teal"], COLORS["gold"], COLORS["orange"]][i])
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("LightGBM robustness and negative-control results", fontsize=14,
                 fontweight="bold", color=COLORS["navy"], pad=24)
    ax.grid(axis="y", alpha=.22)
    ax.legend(ncol=4, loc="lower center", bbox_to_anchor=(.5, -0.22), frameon=False)
    ax.text(.5, 1.01, "Five-fold CV uses development data only; the spatial split is an internal sensitivity check.",
            transform=ax.transAxes, ha="center", fontsize=8.2, color=COLORS["grey"])
    fig.tight_layout()
    save(fig, "Figure_6_lightgbm_robustness")


def main() -> None:
    ensure_directories()
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 140})
    figure_1(); figure_2(); figure_3(); figure_4(); figure_5(); figure_6()
    print(f"Wrote 12 figure files to {FIGURE_DIR}")


if __name__ == "__main__":
    main()
