# Robust Course-of-Action Generation Through Adversarial Self-Play

**Status: SKELETON DRAFT — not submission ready.** This document scaffolds the
paper structure called for in `research design document.md` Section 16
("Minimum Evidence for the Paper"). Sections marked `(projected, pending full
experiment run)` are placeholders describing what we *expect* to report, not
measured results. Sections marked `(measured)` report numbers actually
computed by code in this repository, runnable via `experiments/exp0_baselines.py`.

Target venue: DAI 2026 workshop track / AAAI 2027 main track (per README).

---

## Abstract

*(projected, pending full experiment run)* We study whether LLM-guided,
best-response self-play produces Courses of Action (COAs) that are more
robust to unseen adversarial responses than non-adversarial baselines. We
introduce a synthetic, two-player COA benchmark with a Mission Effectiveness
Function (MEF) and Game-Based Comparison (GBC) score, implement four
baselines (random, greedy-MEF, scripted heuristic, one-shot LLM), and report
held-out worst-case GBC across [N] scenario families. [Headline result to be
inserted once B3/B4 and held-out evaluation are implemented and run.]

## 1. Introduction

Motivation and novelty are adapted from `research design document.md`
Sections 1-3: most planning-evaluation setups score a candidate plan against
a fixed or passive yardstick, which can reward brittle plans. We treat COA
generation as a two-player zero-sum game (BLUE proposes, RED best-responds)
and ask whether iterative adversarial self-play improves *held-out*
robustness rather than just performance against the specific opponent seen
during training.

**Note on scope:** an earlier draft of this project's design doc
(`DESIGN_DOC.md`) proposed a different framing — LOAC compliance and
human-AI collaborative COA generation for real military planning support,
evaluated via a "CCQ" composite metric and SME panels. That framing was
superseded; the implemented system and the second design document
(`research design document.md`) instead study adversarial self-play
robustness on purely synthetic scenarios. This draft follows the
self-play framing actually implemented in `src/coageneration/`. Anyone
reusing this repo for the original LOAC/CCQ research direction will need to
implement the dataset, annotation protocol, and LOAC scorer described in
`DESIGN_DOC.md` from scratch — none of that exists in the current codebase.

## 2. Related Work

*(to be written)* Automated planning (PDDL/classical planners), multi-agent
reinforcement learning self-play (AlphaZero-style), LLM agents in strategic
games, and prior COA-generation / wargaming AI literature. Per the design
doc, no prior work jointly evaluates LLM-generated COAs under an explicit
adversarial best-response with held-out generalization testing — this is the
claimed novelty and should be verified against current literature before
submission.

## 3. Method

### 3.1 Representation (measured / implemented)

`src/coageneration/core.py` defines `GameState` (BLUE/RED `Asset` lists with
capability scores), `CourseOfAction` (a list of typed `Action`s, optionally
organized into a dependency `ChainStep` graph with conditional branches), and
`SelfPlayEngine`, which alternates BLUE/RED moves and degrades asset
capability each round.

### 3.2 Scoring (measured / implemented)

```
MEF(e, c, r) = w_e * effectiveness - w_c * cost - w_r * risk      (w_e=0.5, w_c=0.3, w_r=0.2)
GBC(blue, red) = (blue.mef - red.mef + 2) / 4   ∈ [0, 1]
```

implemented in `src/coageneration/core.py::compute_mef_score` and
`src/coageneration/evaluate.py::gbc_score`. Additional implemented metrics:
`robustness_score` (worst-case MEF across adversarial draws), `coa_diversity`
(mean pairwise Jaccard distance of action-type sets), `action_diversity_score`
(normalized entropy), and a heuristic `doctrinal_alignment_score` rubric
(FM 3-0-inspired; explicitly documented in code as "a benchmark feature
extractor, not a substitute for validation by doctrine experts").

**Caveat:** `nash_gap` is currently `|blue_payoff + red_payoff - 1|`. As
flagged directly in `research design document.md` Section 10, this should
only be called a Nash/exploitability measure once it is derived from valid
game payoffs and actual best-response computation — currently the "best
response" is sampled uniformly at random (see 3.3), so `nash_gap` does not
yet measure equilibrium convergence and should not be reported as such in a
final paper.

### 3.3 Self-play loop (partially implemented)

`SelfPlayEngine.best_response()` either (a) delegates to a supplied `Policy`
(e.g., `LLMPolicy`, which prompts Claude — implemented in
`src/coageneration/llm_policy.py` and exercised in `tests/test_llm_policy.py`
with a mocked client), or (b) falls back to **uniform random action
sampling**. The iterative "BLUE retains/revises candidates using GBC and
robustness scores" step described in the design doc (Section 8, steps 3-5)
is **not yet implemented** — today's `run_episode` runs a fixed number of
alternating rounds without any candidate-selection or revision logic. This
is the single largest gap between the design doc's proposed method and the
current code, and closing it is the top implementation priority before any
self-play-vs-baseline claim can be tested.

### 3.4 Baselines (B0-B2 measured; B3-B4 not yet run)

Implemented in `experiments/exp0_baselines.py`:
- **B0 random**: uniformly sampled valid COA.
- **B1 greedy-MEF**: highest-MEF COA among several randomly generated candidates, no opponent model.
- **B2 scripted heuristic**: fixed recon → assess → attack → withdraw sequence.
- **B3 one-shot LLM** and **B4 random/heuristic self-play**: described in the design doc but not yet wired into an experiment script; `LLMPolicy` exists and is unit-tested but requires `ANTHROPIC_API_KEY` and has not been run as part of a full experiment in this repository.

## 4. Experiments

### 4.1 Experiment 0 — Baseline sanity check (measured)

30 seeds, each baseline evaluated against 5 independently-sampled random RED
responses. Results (from `results/exp0_baselines.json`, generated by
`experiments/exp0_baselines.py`, no LLM calls, fully reproducible without API
keys):

| Baseline | Mean GBC | Stdev GBC | p10 worst-case MEF | Min worst-case MEF | Mean doctrinal alignment | Action diversity (Jaccard) |
|---|---|---|---|---|---|---|
| B0 random | 0.5204 | 0.0293 | -0.0079 | -0.0536 | 0.4947 | 0.7153 |
| B1 greedy-MEF | 0.5533 | 0.0135 | -0.0204 | -0.0536 | 0.4880 | 0.7321 |
| B2 scripted heuristic | 0.4928 | 0.0131 | -0.0204 | -0.0451 | 0.8217 | 0.0000 |

**Interpretation (measured, not projected):** B1 (greedy-MEF) has the
highest mean GBC, but the gap to B0 (random) is small relative to run-to-run
stdev, and the adversary in this run is itself a random policy — so this is
*not* evidence that greedy-MEF is robust against an adaptive opponent, only
that it scores marginally better against a non-adaptive random one. B2
(scripted heuristic) scores highest on doctrinal alignment by construction
(it always performs recon and logistics steps that the rubric rewards) but
has zero action-type diversity across seeds, since it is deterministic by
design. None of this should be read as supporting or refuting H1-H5 in the
design doc — it is a harness sanity check, not the held-out robustness
experiment the hypotheses require.

### 4.2 Experiments 1-4 (LOAC compliance, CCQ comparison, component value, time-constrained performance)

These come from `DESIGN_DOC.md`, the project's original design document, and
describe a **different research program** (human-AI collaborative COA
generation with LOAC compliance scoring) than the adversarial self-play
system actually implemented. **No code in this repository implements the
COA-Bench dataset, LOAC compliance scorer, CCQ metric, or human-AI
collaboration protocol described there.** All numbers in `DESIGN_DOC.md`'s
"Expected results" tables (e.g., "Human CCQ ≈ 0.82," "Claude + doctrine RAG
LOAC violation rate 0.08") are explicitly labeled as *hypothesized* expected
results in that document, not measured outcomes — but we flag this
prominently here because a reader skimming the repo could otherwise mistake
the design doc's expected-result tables for completed experiments.

### 4.3 Self-play robustness experiment *(projected, pending full experiment run)*

Per `research design document.md` Sections 7-12: held-out adversary
evaluation, full ablation suite, ≥30 seeds, paired bootstrap significance
tests, and qualitative failure analysis. None of this has been run. This is
the core remaining work — see `results/README.md` for the current gap list.

## 5. Limitations

- Adversary "best response" is currently random, not optimized — see 3.3.
- No held-out scenario/opponent split exists yet.
- `doctrinal_alignment_score` is a keyword/structure heuristic, explicitly not validated by doctrine experts.
- All scenarios and assets are synthetic; no claims about real operational planning are supported by current results.
- B3/B4 LLM-involving experiments require API access and have not been executed end-to-end as part of an automated experiment.

## 6. Reproducibility

```bash
pip install -e .
pytest tests/ -v                      # 57 tests, no API key required
python scripts/run_demo.py            # random-policy self-play demo
python experiments/exp0_baselines.py  # writes results/exp0_baselines.json
```
