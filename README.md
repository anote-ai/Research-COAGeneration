# Research COAGeneration

This repository is organized around two independent research papers and their
reproducible experiments:

1. **COA paper:** adversarial course-of-action generation with game-theoretic
   multi-agent evaluation.
2. **Meta-routing paper:** meta-decision policies for agentic systems, including
   when to decompose, retrieve, execute code, delegate, verify, or answer.

Shared implementation code lives under `src/`, while experiments, papers, and
results are project-first:

```text
experiments/
  coa/                    # COA-Bench experiment runner
  meta-routing/           # DAI/AAAI meta-routing runners
papers/
  coa/                    # COA paper drafts by venue
  meta-routing/           # Meta-routing paper drafts by venue
results/
  coa/                    # COA generated artifacts
  meta-routing/           # Meta-routing generated artifacts
```

**Disclaimer:** This repository is for academic research only. COA scenarios,
assets, and strategies are entirely synthetic and do not represent any real
military doctrine, operations, or advice.

## COA Paper

The COA track studies adversarial course-of-action generation as a small
multi-agent game. BLUE policies produce structured COAs, RED policies sample
adversarial responses, and a council policy proposes, stress-tests, revises, and
adjudicates candidate plans.

```bash
python experiments/coa/run_benchmark.py
```

Primary locations:

- `src/coageneration/`: COA data structures, policies, metrics, and synthetic scenario generators
- `experiments/coa/`: reproducible COA experiment runner
- `papers/coa/coa-bench/dai2026/`: DAI Industry Track COA paper
- `papers/coa/coa-bench/aaai2027/`: AAAI COA paper
- `results/coa/coa-bench/main/`: COA benchmark outputs

## MetaRoute-Bench

The meta-routing track contains `metarouter`, an independent benchmark for the
meta-decision layer of agentic systems. It compares when policies decompose, use
tools, execute code, delegate, verify, and answer directly across synthetic
data-analysis, research, and document-processing workload profiles.

The AAAI study adds a raw-text, budget-aware router and an executable benchmark
with exact answer checking. The earlier DAI results remain an explicit seeded
offline execution model. Neither study claims production or live-LLM results.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
metarouter-benchmark --seeds 30 --output results/meta-routing/dai2026/main
python experiments/meta-routing/dai2026/run_ablations.py
python experiments/meta-routing/dai2026/plot_results.py
python experiments/meta-routing/dai2026/check_paper_results.py
python experiments/meta-routing/aaai2027/run_executable.py
python experiments/meta-routing/aaai2027/run_ablations.py
python experiments/meta-routing/aaai2027/plot_executable.py
pytest -q
```

Primary locations:

- `src/metarouter/`: meta-routing models, policies, simulator, and executable benchmark
- `experiments/meta-routing/dai2026/`: DAI meta-routing benchmark runners
- `experiments/meta-routing/aaai2027/`: AAAI executable benchmark runners
- `papers/meta-routing/dai2026/`: DAI Industry Track meta-routing paper
- `papers/meta-routing/aaai2027/`: AAAI meta-routing paper
- `results/meta-routing/`: generated meta-routing artifacts

## COA-Bench Metrics

The COA-Bench implementation uses synthetic evaluation metrics for offline
benchmarking:

- `quality_score`: an internal scalar **COA quality score** combining effectiveness,
  cost, and risk.
- `advantage_score`: an internal **BLUE-vs-RED advantage score** derived from the
  two COA quality scores.

A **Course of Action (COA)** is assigned an internal quality score:

```
quality(e, c, r) = w_e * effectiveness - w_c * cost - w_r * risk
```

where `w_e=0.5, w_c=0.3, w_r=0.2` by default, clamped to `[-1, 1]`.

The internal BLUE-vs-RED advantage score is:

```
advantage(blue, red) = (blue.quality - red.quality + 2) / 4  ∈ [0, 1]
```

## Game-Theoretic Formulation

The problem is modelled as a two-player zero-sum game:
- **State**: `GameState` — lists of BLUE/RED assets with capability scores
- **Action**: `CourseOfAction` — ordered list of tactical actions
- **Payoff**: internal COA quality score (BLUE maximises, RED minimises)
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
python experiments/coa/run_benchmark.py
pytest tests/ -v
```

## Reproducing all results

```bash
./run_all.sh
```

Runs the full test suite, the COAGeneration self-play demo, the metarouter
benchmark (30 seeds), ablations, figure generation, and paper-claim
verification in one command. No GPU or API keys required — everything uses
the offline seeded simulator and synthetic scenario generators. Expected
runtime: ~5-10 minutes on a laptop.

## License

MIT — see [LICENSE](LICENSE).

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
