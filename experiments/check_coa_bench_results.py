#!/usr/bin/env python3
"""Verify that results/coa-bench/main/summary.csv matches the numbers reported
in papers/coa-bench/main.tex, within a tolerance of 0.002.

Run after experiments/coa_bench_experiment.py to confirm the paper numbers
are backed by the committed artifacts.

Usage:
    python experiments/check_coa_bench_results.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

SUMMARY_CSV = Path("results/coa-bench/main/summary.csv")
TOLERANCE = 0.002

# Numbers as they appear in papers/coa-bench/main.tex Table 1 and body text.
PAPER_NUMBERS: dict[str, dict[str, float]] = {
    "gbc_single":                    {"mean": 0.524, "ci_lower": 0.519, "ci_upper": 0.530},
    "gbc_sampled":                   {"mean": 0.490, "ci_lower": 0.487, "ci_upper": 0.494},
    "nash_gap_single":               {"mean": 0.199, "ci_lower": 0.189, "ci_upper": 0.209},
    "nash_gap_sampled":              {"mean": 0.267, "ci_lower": 0.261, "ci_upper": 0.274},
    "red_doctrinal_alignment_single":  {"mean": 0.667, "ci_lower": 0.640, "ci_upper": 0.695},
    "red_doctrinal_alignment_sampled": {"mean": 0.678, "ci_lower": 0.658, "ci_upper": 0.700},
    "candidate_diversity":           {"mean": 0.732, "ci_lower": 0.720, "ci_upper": 0.745},
    "candidate_mef_spread":          {"mean": 0.254, "ci_lower": 0.245, "ci_upper": 0.264},
    "n_pareto_optimal":              {"mean": 2.149, "ci_lower": 1.978, "ci_upper": 2.333},
    "gbc_llm":                       {"mean": 0.549, "ci_lower": 0.546, "ci_upper": 0.552},
    "nash_gap_llm":                  {"mean": 0.150, "ci_lower": 0.143, "ci_upper": 0.157},
    "red_doctrinal_alignment_llm":   {"mean": 0.804, "ci_lower": 0.780, "ci_upper": 0.831},
    "framing_sensitivity_delta":     {"mean": 0.045, "ci_lower": 0.045, "ci_upper": 0.045},
}


def load_summary(path: Path) -> dict[str, dict[str, float]]:
    rows: dict[str, dict[str, float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows[row["metric"]] = {
                "mean": float(row["mean"]),
                "ci_lower": float(row["ci_lower"]),
                "ci_upper": float(row["ci_upper"]),
            }
    return rows


def main() -> None:
    if not SUMMARY_CSV.exists():
        print(f"ERROR: {SUMMARY_CSV} not found. Run experiments/coa_bench_experiment.py first.")
        sys.exit(1)

    actual = load_summary(SUMMARY_CSV)
    failures: list[str] = []

    for metric, expected in PAPER_NUMBERS.items():
        if metric not in actual:
            failures.append(f"  MISSING metric: {metric}")
            continue
        for field, exp_val in expected.items():
            act_val = actual[metric][field]
            diff = abs(act_val - exp_val)
            if diff > TOLERANCE:
                failures.append(
                    f"  MISMATCH {metric}.{field}: "
                    f"paper={exp_val:.4f}, actual={act_val:.4f}, diff={diff:.4f}"
                )

    if failures:
        print(f"FAIL — {len(failures)} mismatch(es) found (tolerance={TOLERANCE}):")
        for msg in failures:
            print(msg)
        sys.exit(1)
    else:
        print(f"OK — all {len(PAPER_NUMBERS)} paper numbers match summary.csv "
              f"within tolerance={TOLERANCE}")


if __name__ == "__main__":
    main()
