# COAGeneration

> **Game-theoretic Course-of-Action Generation via Self-Play**

COAGeneration benchmarks AI systems on the military planning problem of generating
robust Courses of Action (COAs) against adaptive adversaries using game-theoretic
self-play.

**Disclaimer:** This repository is for academic research only. All scenarios,
assets, and strategies are entirely synthetic and do not represent any real
military doctrine, operations, or advice.

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
python experiments/exp0_baselines.py   # real baseline comparison, writes results/exp0_baselines.json
pytest tests/ -v
```

## Project status & documents

This repo currently contains **two design documents that describe different
research framings**:

- `research design document.md` — adversarial self-play / MEF / GBC robustness
  study. This is the framing the current codebase (`src/coageneration/`)
  actually implements.
- `DESIGN_DOC.md` — an earlier framing centered on LOAC compliance and
  human-AI collaborative COA generation (CCQ metric, COA-Bench dataset, SME
  annotation). **No code in this repo implements that framing's dataset,
  LOAC scorer, CCQ metric, or annotation protocol.** Treat `DESIGN_DOC.md` as
  superseded/aspirational unless that work is explicitly revived.

Other docs:
- `PAPER_DRAFT.md` — paper skeleton; clearly separates measured results from
  projected/not-yet-run sections.
- `BLOG.md` — plain-language project summary.
- `results/README.md` — what experiment output exists, what's missing, and
  how to regenerate it.

See `results/exp0_baselines.json` for the first real (LLM-free) baseline
comparison (B0 random / B1 greedy-MEF / B2 scripted heuristic), run over 30
seeds. B3 (one-shot LLM) and B4 (LLM self-play) baselines from the design doc
are implemented in `src/coageneration/llm_policy.py` but have not yet been
run as part of an automated experiment (they require `ANTHROPIC_API_KEY`).

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
