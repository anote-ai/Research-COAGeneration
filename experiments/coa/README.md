# COA Experiments

This folder contains the experiment runner for the COA paper track.

Run from the repository root:

```bash
python experiments/coa/run_benchmark.py
```

The runner writes reproducible artifacts to `results/coa/coa-bench/main/`.
It uses the shared `src/coageneration` package and does not call live models,
external services, classified data, or real planning systems.
