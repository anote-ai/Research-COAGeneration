"""Plot held-out executable benchmark tradeoffs for the AAAI manuscript."""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

import matplotlib.pyplot as plt


def main() -> None:
    result_dir = Path("results/meta-routing/aaai2027/executable")
    challenge_dir = Path("results/meta-routing/aaai2027/challenge")
    standard_rows = list(
        csv.DictReader((result_dir / "summary.csv").open(encoding="utf-8"))
    )
    challenge_rows = list(
        csv.DictReader((challenge_dir / "summary.csv").open(encoding="utf-8"))
    )
    selected_names = {
        "direct",
        "keyword",
        "learned_one_shot",
        "learned_budget",
        "static_workload",
        "fixed_agent",
        "oracle",
    }
    labels = {
        "direct": "Direct",
        "keyword": "Keyword",
        "learned_one_shot": "One-shot",
        "learned_budget": "Learned",
        "static_workload": "Static",
        "fixed_agent": "Fixed agent",
        "oracle": "Oracle",
    }
    colors = {
        "learned_budget": "#087f5b",
        "oracle": "#1c7ed6",
        "static_workload": "#e67700",
        "fixed_agent": "#c92a2a",
    }
    left_offsets = {
        "oracle": (-34, -13),
        "learned_budget": (5, 5),
        "static_workload": (5, 4),
        "fixed_agent": (5, -12),
        "keyword": (5, 4),
        "learned_one_shot": (5, -12),
        "direct": (5, 4),
    }
    challenge_offsets = {
        "oracle": (-34, -13),
        "static_workload": (5, 4),
        "fixed_agent": (5, -12),
        "learned_budget": (5, 4),
        "keyword": (5, 4),
        "learned_one_shot": (5, 4),
        "direct": (5, 4),
    }

    figure, axes = plt.subplots(1, 2, figsize=(7.0, 2.55))
    for axis, rows, offsets in (
        (axes[0], standard_rows, left_offsets),
        (axes[1], challenge_rows, challenge_offsets),
    ):
        for row in rows:
            name = row["policy"]
            if name not in selected_names:
                continue
            success = float(row["success_rate"])
            cost = float(row["mean_cost"])
            color = colors.get(name, "#495057")
            axis.scatter(cost, success, color=color, s=34)
            axis.annotate(
                labels[name],
                (cost, success),
                xytext=offsets[name],
                textcoords="offset points",
                fontsize=7,
            )

    axes[0].set_title("Held-out test")
    axes[1].set_title("Lexical-shift challenge")
    axes[0].set_xlabel("Mean normalized route cost")
    axes[0].set_ylabel("Machine-checked success")
    axes[1].set_xlabel("Mean normalized route cost")
    for axis in axes:
        axis.set_ylim(0.2, 1.08)
        axis.grid(alpha=0.2, linewidth=0.6)
    figure.tight_layout()

    pdf = result_dir / "executable_tradeoffs.pdf"
    png = result_dir / "executable_tradeoffs.png"
    figure.savefig(pdf, bbox_inches="tight")
    figure.savefig(png, dpi=220, bbox_inches="tight")
    plt.close(figure)

    paper_dir = Path("papers/meta-routing/aaai2027/figures")
    paper_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, paper_dir / pdf.name)
    shutil.copyfile(png, paper_dir / png.name)
    print(f"Wrote {pdf} and {png}")


if __name__ == "__main__":
    main()
