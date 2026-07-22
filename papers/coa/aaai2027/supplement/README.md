# Anonymous COA-Bench Supplement

This package reproduces the adversarial course-of-action benchmark reported in
the AAAI submission.

## Environment

- Python 3.10 or newer
- Pydantic and pytest
- No API key, network service, GPU, classified data, real intelligence data, or
  proprietary dataset is required

## Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python experiments/coa/aaai2027/run_benchmark.py
pytest -q tests/test_core.py tests/test_data.py tests/test_evaluate.py tests/test_llm_policy.py
```

The run creates 50 synthetic scenarios from 10 seeds and five operational
templates. It exports per-scenario rows, response-budget curves, council traces,
terrain summaries, bootstrap summaries, and run metadata to
`results/coa/aaai2027/main/`.

## Contents

- `src/coageneration/`: typed COA representation, scenario generators, policies,
  and evaluation metrics
- `experiments/coa/aaai2027/`: AAAI COA experiment entrypoint
- `experiments/coa/shared/`: shared experiment implementation
- `results/coa/aaai2027/`: reported artifacts
- `tests/`: focused unit tests for COA representation, data, evaluation, and
  policy behavior

The package is released under the MIT License.
