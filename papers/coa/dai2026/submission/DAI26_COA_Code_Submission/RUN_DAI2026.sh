#!/usr/bin/env bash
# Reproduce the DAI 2026 COA benchmark artifact from this code package.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

python -m pip install -e ".[dev]"
python -m pytest tests/ -v
python scripts/run_demo.py
python experiments/coa/dai2026/run_benchmark.py

echo "DAI 2026 artifacts written to results/coa/dai2026/main/"
