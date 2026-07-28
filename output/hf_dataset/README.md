---
license: mit
pretty_name: Research COAGeneration
tags:
- synthetic-data
- benchmark
- multi-agent-systems
- game-theory
- course-of-action-generation
- adversarial-planning
- agentic-systems
- meta-routing
---

# Research COAGeneration Dataset

This dataset contains synthetic benchmark outputs from the Research
COAGeneration repository. It can include the COA track, the meta-routing track,
or both, depending on which folders were uploaded.

## Contents

- `data/coa/dai2026/main/` - DAI 2026 COA benchmark outputs
- `data/coa/aaai2027/main/` - AAAI 2027 COA benchmark outputs
- `data/meta-routing/dai2026/` - DAI 2026 meta-routing benchmark outputs
- `data/meta-routing/aaai2027/` - AAAI 2027 executable, challenge, ablation,
  and sensitivity outputs

COA result folders contain per-scenario rows, summary tables, response-budget
curves, council traces, terrain summaries, rubric validation where available,
and run metadata. Meta-routing folders contain task splits, traces, comparisons,
summaries, ablations, sensitivity tables, and generated figures where available.

## Important Use Notice

This dataset is for academic research only. COA scenarios, assets, policies,
and strategies are synthetic and do not represent real military doctrine,
operations, or advice. Meta-routing tasks and traces are synthetic/offline
benchmark artifacts and do not claim production or live-LLM behavior unless
explicitly stated in the source paper or repository.

## License

MIT. See the source repository license for details.
