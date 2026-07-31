# DAI 2026 COA Code Submission

This ZIP contains the code and generated artifacts for the DAI 2026 Industry Track submission:

Adversarial Course-of-Action Generation: Game-Theoretic Multi-Agent Algorithms for COA matching & COA generation

## Contents

- `src/coageneration/`: COA data structures, policies, metrics, and synthetic scenario generation.
- `experiments/coa/dai2026/run_benchmark.py`: DAI 2026 benchmark entrypoint.
- `experiments/coa/shared/benchmark.py`: shared benchmark implementation.
- `results/coa/dai2026/main/`: generated CSV/JSON artifacts reported in the paper.
- `tests/`: unit tests for core COA functionality.
- `README.md`, `pyproject.toml`, `requirements.txt`, `LICENSE`: setup and project metadata.

The package intentionally excludes LaTeX paper source, local build directories, cached bytecode, and unrelated AAAI 2027 artifacts.

## Reproduce

From the unzipped package root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
./RUN_DAI2026.sh
```

The benchmark writes outputs to `results/coa/dai2026/main/`.

## Data And Safety

All scenarios, assets, and COAs are synthetic. The artifact uses no classified data, real intelligence data, proprietary data, human-subject data, operational systems, or external API calls.
