#!/usr/bin/env bash
# Reproduce every COA result, table, and artifact in this repository from scratch.
#
# Usage:
#   ./run_all.sh
#
# No GPU or API keys required. Everything here uses offline synthetic scenario
# generators.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "==> Installing dependencies (editable install, dev extras)"
python -m pip install -e ".[dev]"

echo "==> Running COA test suite"
python -m pytest tests/ -v

echo "==> Running coageneration self-play demo"
python scripts/run_demo.py

echo "==> Running DAI COA benchmark"
python experiments/coa/dai2026/run_benchmark.py

echo "==> Running AAAI COA benchmark"
python experiments/coa/aaai2027/run_benchmark.py

echo ""
echo "==> Done. Artifacts written to results/coa/{dai2026,aaai2027}/main/"
