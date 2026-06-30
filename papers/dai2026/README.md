# DAI 2026 Industry Paper

The manuscript is `main.tex`; references are in `references.bib`. Author names
and affiliations are placeholders and must be replaced before submission.

The reported numbers come from committed experiment artifacts generated with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
metarouter-benchmark --seeds 30 --output results/dai2026/main
python experiments/dai2026/run_ablations.py
python experiments/dai2026/plot_results.py
python experiments/dai2026/check_paper_results.py
pytest -q
```

Important boundary: the results use a seeded offline execution model. They must not be described as production, human-subject, or live-LLM results.

## Venue Contribution

The DAI contribution is the transparent evaluation framework, operational policy
comparison, trace artifact, and deployment lessons. It does not claim a learned
routing algorithm or live-system effectiveness.
