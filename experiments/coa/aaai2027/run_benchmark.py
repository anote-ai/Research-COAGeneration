#!/usr/bin/env python3
"""Run the COA experiment for the AAAI 2027 paper."""

from __future__ import annotations

from pathlib import Path
import sys

SHARED = Path(__file__).resolve().parents[1] / "shared"
sys.path.insert(0, str(SHARED))

from benchmark import main  # noqa: E402


if __name__ == "__main__":
    main(
        default_output=Path("results/coa/aaai2027/main"),
        venue="aaai2027",
        source_script="experiments/coa/aaai2027/run_benchmark.py",
        default_n_seeds=30,
        include_llm_baseline=True,
        include_rubric_validation=True,
    )
