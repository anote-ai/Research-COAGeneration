# DAI 2026 Paper Artifact

The paper draft is `dai2026.tex`; references are in `references.bib`. Author names and affiliations are placeholders and must be replaced before submission.

The reported numbers come from committed experiment artifacts generated with:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
metarouter-benchmark --seeds 30 --output results/metarouter
python scripts/run_metarouter_ablations.py
pytest -q
```

Important boundary: the results use a seeded offline execution model. They must not be described as production, human-subject, or live-LLM results.

