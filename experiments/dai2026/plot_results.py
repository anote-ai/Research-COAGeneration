#!/usr/bin/env python3
"""Generate the DAI paper's success/cost/latency figure from summary.csv."""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "metarouter-matplotlib")
)

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results/metarouter/summary.csv"
OUTPUT_DIR = ROOT / "paper/figures"


def main() -> None:
    with SUMMARY.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    labels = {
        "adaptive": "Adaptive",
        "static_workload": "Static",
        "one_shot": "One-shot",
        "always_tool": "Tool",
        "always_decompose": "Decompose",
        "always_code": "Code",
        "random": "Random",
        "direct": "Direct",
    }
    colors = {
        "adaptive": "#c44e52",
        "static_workload": "#4c72b0",
        "one_shot": "#55a868",
    }

    plt.rcParams.update({"font.size": 8, "font.family": "serif"})
    figure, axes = plt.subplots(1, 2, figsize=(6.7, 2.55), sharey=True)
    dimensions = (("mean_cost", "Mean normalized cost"), ("mean_latency_s", "Mean latency (s)"))

    for axis, (field, xlabel) in zip(axes, dimensions):
        for row in rows:
            policy = row["policy"]
            x = float(row[field])
            y = 100 * float(row["success_rate"])
            yerr = 100 * float(row["success_ci95"])
            axis.errorbar(
                x,
                y,
                yerr=yerr,
                fmt="o",
                markersize=5.2 if policy in colors else 4.2,
                capsize=2,
                color=colors.get(policy, "#777777"),
                zorder=3,
            )
            offset = (3, 4) if policy not in {"random", "always_tool"} else (3, -9)
            axis.annotate(
                labels[policy],
                (x, y),
                xytext=offset,
                textcoords="offset points",
                fontsize=7,
            )
        axis.set_xlabel(xlabel)
        axis.grid(axis="both", color="#dddddd", linewidth=0.6, zorder=0)
        axis.spines[["top", "right"]].set_visible(False)

    axes[0].set_ylabel("Task success (%)")
    figure.tight_layout(w_pad=1.4)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_DIR / "success_cost_latency.pdf", bbox_inches="tight")
    figure.savefig(OUTPUT_DIR / "success_cost_latency.png", dpi=220, bbox_inches="tight")
    plt.close(figure)
    print(f"Wrote paper figure to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
