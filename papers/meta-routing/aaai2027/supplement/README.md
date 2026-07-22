# Anonymous Executable Meta-Routing Supplement

This package reproduces the executable benchmark, learned raw-text router,
baselines, paired comparisons, ablations, and paper figure.

## Environment

- Python 3.10 or newer
- NumPy, Matplotlib, and pytest
- No API key, network service, GPU, or proprietary dataset is required

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python experiments/meta-routing/aaai2027/run_executable.py
python experiments/meta-routing/aaai2027/run_ablations.py
python experiments/meta-routing/aaai2027/run_sensitivity.py
python experiments/meta-routing/aaai2027/plot_executable.py
python experiments/meta-routing/aaai2027/check_paper_results.py
pytest -q tests/test_executable_metarouter.py
```

The main run creates 216 training, 72 development, 108 test, and 108 locked
lexical-shift challenge tasks. Prompt templates are disjoint by split.
Operations execute locally and answers are checked exactly. Cost is normalized
operation usage; latency is local CPU time, not live-model or network latency.

## Contents

- `src/metarouter/`: task generation, operation execution, learned router,
  baselines, metrics, and exports
- `experiments/meta-routing/aaai2027/`: main run, ablations, plotting, and result checks
- `tests/`: focused executable benchmark tests
- `results/meta-routing/aaai2027/`: reported task-level traces and aggregate artifacts

The package is released under the MIT License.
