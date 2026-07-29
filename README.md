# Research COAGeneration

This repository contains the COA-Bench research project: adversarial
course-of-action generation with game-theoretic multi-agent evaluation.

Meta-routing artifacts have been separated into the sibling project
`../Research-MetaRouting`. COAGeneration should contain only COA source code,
experiments, papers, results, and dataset tooling.

```text
src/coageneration/      # COA data structures, policies, metrics, generators
experiments/coa/        # DAI/AAAI COA experiment runners and shared logic
papers/coa/             # COA paper drafts and submission artifacts
results/coa/            # COA generated benchmark artifacts
scripts/                # COA demo and dataset upload utilities
tests/                  # COA unit tests
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
python experiments/coa/dai2026/run_benchmark.py
python experiments/coa/aaai2027/run_benchmark.py
```

Primary locations:

- `src/coageneration/`: COA data structures, policies, metrics, and synthetic scenario generators
- `experiments/coa/dai2026/`: DAI COA experiment entrypoint
- `experiments/coa/aaai2027/`: AAAI COA experiment entrypoint
- `experiments/coa/shared/`: shared COA experiment implementation
- `papers/coa/dai2026/`: DAI Industry Track COA paper
- `papers/coa/aaai2027/`: AAAI COA paper
- `results/coa/dai2026/main/`: DAI COA benchmark outputs
- `results/coa/aaai2027/main/`: AAAI COA benchmark outputs

## COA-Bench Metrics

The COA-Bench implementation uses synthetic evaluation metrics for offline
benchmarking:

- `quality_score`: an internal scalar **COA quality score** combining effectiveness,
  cost, and risk.
- `advantage_score`: an internal **BLUE-vs-RED advantage score** derived from the
  two COA quality scores.

A **Course of Action (COA)** is assigned an internal quality score:

```text
quality(e, c, r) = w_e * effectiveness - w_c * cost - w_r * risk
```

where `w_e=0.5, w_c=0.3, w_r=0.2` by default, clamped to `[-1, 1]`.

The internal BLUE-vs-RED advantage score is:

```text
advantage(blue, red) = (blue.quality - red.quality + 2) / 4 in [0, 1]
```

## Game-Theoretic Formulation

The problem is modelled as a two-player zero-sum game:

- **State**: `GameState` - lists of BLUE/RED assets with capability scores
- **Action**: `CourseOfAction` - ordered list of tactical actions
- **Payoff**: internal COA quality score, maximized by BLUE and minimized by RED
- **Equilibrium**: Nash gap = `|blue_payoff + red_payoff - 1|` (0 at equilibrium)

## Self-Play Algorithm

```text
initialise GameState
for round in 1..N:
    blue_coa = blue_policy(state)
    red_coa  = best_response(blue_coa, state)
    state    = transition(state, blue_coa, red_coa)
return episode_summary(states)
```

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python scripts/run_demo.py
python experiments/coa/dai2026/run_benchmark.py
python experiments/coa/aaai2027/run_benchmark.py
pytest tests/ -v
```

## Reproducing COA Results

```bash
./run_all.sh
```

Runs the COA test suite, the self-play demo, both COA benchmark entrypoints, and
paper-claim checks where available. No GPU or API keys required.

## License

MIT - see [LICENSE](LICENSE).

## Venues

- **DAI 2026** - Distributed AI workshop
- **AAAI 2027** - Main track, Game Theory and Multi-Agent Systems

## Citation

```bibtex
@misc{coageneration2026,
  title   = {COAGeneration: Self-Play Benchmarks for Adversarial Course-of-Action Planning},
  author  = {Anote AI},
  year    = {2026},
  url     = {https://github.com/anote-ai/research-coageneration}
}
```
