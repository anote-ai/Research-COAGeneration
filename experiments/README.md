# Experiments

Experiments are organized by paper track first, then by venue when a track has
multiple submissions.

- `coa/`: COA-Bench adversarial course-of-action experiments.
- `meta-routing/dai2026/`: DAI Industry Track meta-routing system benchmark.
- `meta-routing/aaai2027/`: AAAI executable meta-routing benchmark.
- `oracle2026/`: placeholder for multilingual/cultural reasoning extensions.
- `shared/`: shared statistical and export utilities.

Shared implementation belongs in `src/coageneration` or `src/metarouter`;
experiment folders should contain runners, checks, plotting scripts, and
packaging utilities only.
