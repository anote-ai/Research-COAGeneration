#!/usr/bin/env python3
"""Run the COA experiment for the DAI 2026 Industry Track paper."""

from __future__ import annotations

from pathlib import Path
import sys

SHARED = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED))

from benchmark import main  # noqa: E402


if __name__ == "__main__":
    main(
        default_output=Path("results/coa/dai2026/main"),
        venue="dai2026",
        source_script="experiments/coa/dai2026/run_benchmark.py",
    )
