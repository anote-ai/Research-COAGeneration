#!/usr/bin/env python3
"""Fail if headline paper values drift from generated result artifacts."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_indexed(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def close(actual: str, expected: float, tolerance: float = 5e-4) -> None:
    if abs(float(actual) - expected) > tolerance:
        raise AssertionError(f"expected {expected}, found {actual}")


def main() -> None:
    summary = read_indexed(ROOT / "results/dai2026/main/summary.csv", "policy")
    close(summary["adaptive"]["success_rate"], 0.7944444444)
    close(summary["static_workload"]["success_rate"], 0.7670370370)
    close(summary["one_shot"]["success_rate"], 0.6742592593)
    close(summary["direct"]["success_rate"], 0.5290740741)
    close(summary["adaptive"]["mean_cost"], 2.9123633333)
    close(summary["adaptive"]["mean_latency_s"], 20.4513333333)

    comparisons = read_indexed(
        ROOT / "results/dai2026/main/comparisons.csv", "baseline"
    )
    close(comparisons["static_workload"]["success_difference"], 0.0274074074)
    close(comparisons["one_shot"]["success_difference"], 0.1201851852)

    ablations = read_indexed(
        ROOT / "results/dai2026/ablations/summary.csv", "policy"
    )
    close(ablations["adaptive_no_verify"]["success_rate"], 0.7474074074)
    close(ablations["adaptive_single_action"]["success_rate"], 0.6814814815)
    print("Paper headline results match generated artifacts.")


if __name__ == "__main__":
    main()
