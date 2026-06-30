#!/usr/bin/env bash
# Reproduce every result, table, and figure in this repository from scratch.
#
# Usage:
#   ./run_all.sh
#
# Expected runtime: ~5-10 minutes on a laptop (dominated by the metarouter
# benchmark's 30-seed run). No GPU or API keys required — everything here
# uses the offline seeded simulator and synthetic scenario generators.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

echo "==> Installing dependencies (editable install, dev extras)"
python -m pip install -e ".[dev]"

echo "==> Running full test suite (coageneration + metarouter)"
python -m pytest tests/ -v

echo "==> Running coageneration self-play demo"
python scripts/run_demo.py

echo "==> Running metarouter benchmark (30 seeds, 8 policies)"
python -m metarouter.cli --seeds 30 --output results/dai2026/main

echo "==> Running metarouter adaptive-policy ablations"
python experiments/dai2026/run_ablations.py

echo "==> Generating figures from benchmark results"
python experiments/dai2026/plot_results.py

echo "==> Verifying generated results match paper claims"
python experiments/dai2026/check_paper_results.py

echo ""
echo "==> Done. Artifacts written to results/dai2026/{main,ablations}/"
echo "    Figures written to papers/dai2026/figures/"
