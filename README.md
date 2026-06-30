# COAGeneration

> **Game-theoretic Course-of-Action Generation via Self-Play**

COAGeneration benchmarks AI systems on the military planning problem of generating
robust Courses of Action (COAs) against adaptive adversaries using game-theoretic
self-play.

**Disclaimer:** This repository is for academic research only. All scenarios,
assets, and strategies are entirely synthetic and do not represent any real
military doctrine, operations, or advice.

## MetaRoute-Bench

The repository also contains `metarouter`, an independent benchmark for the
meta-decision layer of agentic systems. It compares when policies decompose,
use tools, execute code, delegate, verify, and answer directly across synthetic
data-analysis, research, and document-processing workload profiles.

The current results come from an explicit seeded offline execution model. They
are useful for testing evaluation methodology and policy tradeoffs, but they are
not production or live-LLM results.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
metarouter-benchmark --seeds 30 --output results/metarouter
python scripts/run_metarouter_ablations.py
python scripts/check_paper_results.py
pytest -q
```

The DAI 2026 draft and literature notes are under `paper/`. Generated summaries,
task profiles, comparisons, ablations, and raw traces are under `results/`.

## MEF + GBC Problem Framing

A **Course of Action (COA)** is scored by the **Mission Effectiveness Function (MEF)**:

```
MEF(e, c, r) = w_e * effectiveness - w_c * cost - w_r * risk
```

where `w_e=0.5, w_c=0.3, w_r=0.2` by default, clamped to `[-1, 1]`.

The **Game-Based Comparison (GBC)** score compares BLUE and RED COAs:

```
GBC(blue, red) = (blue.mef - red.mef + 2) / 4  ∈ [0, 1]
```

## Game-Theoretic Formulation

The problem is modelled as a two-player zero-sum game:
- **State**: `GameState` — lists of BLUE/RED assets with capability scores
- **Action**: `CourseOfAction` — ordered list of tactical actions
- **Payoff**: MEF score (BLUE maximises, RED minimises)
- **Equilibrium**: Nash gap = `|blue_payoff + red_payoff - 1|` (0 at equilibrium)

## Self-Play Algorithm

```
initialise GameState
for round in 1..N:
    blue_coa = blue_policy(state)
    red_coa  = best_response(blue_coa, state)
    state    = transition(state, blue_coa, red_coa)
return episode_summary(states)
```

## Quickstart

```bash
pip install -e .
python scripts/run_demo.py
pytest tests/ -v
```

## Venues

- **DAI 2026** — Distributed AI workshop
- **AAAI 2027** — Main track, Game Theory and Multi-Agent Systems

## Citation

```bibtex
@misc{coageneration2026,
  title   = {COAGeneration: Self-Play Benchmarks for Adversarial Course-of-Action Planning},
  author  = {Anote AI},
  year    = {2026},
  url     = {https://github.com/anote-ai/research-coageneration}
}
```
