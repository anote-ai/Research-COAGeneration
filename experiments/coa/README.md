# COA Experiments

This folder contains venue-specific experiment entrypoints for the COA paper
track.

Run from the repository root:

```bash
python experiments/coa/dai2026/run_benchmark.py
python experiments/coa/aaai2027/run_benchmark.py
```

Both entrypoints call the shared implementation in `shared/benchmark.py` and
write venue-scoped artifacts:

- `results/coa/dai2026/main/`
- `results/coa/aaai2027/main/`

The runners use the shared `src/coageneration` package and do not call live
models, external services, classified data, or real planning systems.
