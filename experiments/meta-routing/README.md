# Meta-Routing Experiments

This folder contains experiment runners for the meta-routing paper track.

- `dai2026/`: DAI Industry Track benchmark, ablations, plotting, and paper checks.
- `aaai2027/`: AAAI executable benchmark, challenge split, sensitivity analysis,
  packaging, and paper checks.

Run from the repository root:

```bash
python -m metarouter.cli --seeds 30 --output results/meta-routing/dai2026/main
python experiments/meta-routing/dai2026/run_ablations.py
python experiments/meta-routing/aaai2027/run_executable.py
```

The runners use the shared `src/metarouter` package.
