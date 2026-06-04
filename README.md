# Adversarial Course-of-Action Generation

> Game-Theoretic Multi-Agent Algorithms for MEF & GBC

This repository implements LLM-guided best-response self-play for **Most-Effective-Force (MEF)** and **Game-Based COA (GBC)** generation in wargaming scenarios. The framework frames wargaming course-of-action planning as a multi-agent game and evaluates generated COAs in a simulated wargame environment.

---

## Defense / Security Disclaimer

This software is intended solely for **academic research**, simulation, and educational purposes. All wargaming scenarios are fictitious and do not represent real military operations, plans, or capabilities. Users are responsible for ensuring compliance with applicable laws and regulations. The authors do not endorse use of this work for offensive military operations.

---

## Problem Framing

### Most-Effective-Force (MEF)

MEF analysis identifies the minimum force package required to achieve an objective with acceptable risk. The MEF score is a weighted composite:

```
MEF = w_e * effectiveness - w_c * cost - w_r * risk
```

Default weights: w_e=0.5, w_c=0.3, w_r=0.2.

### Game-Based COA (GBC)

GBC frames COA planning as a two-player zero-sum game between BLUE (friendly) and RED (adversary) forces. Each player selects a COA, and payoffs are determined by the resulting game state. Equilibrium analysis identifies robust COAs.

---

## Game-Theoretic Formulation

| Concept | Description |
|---------|-------------|
| Players | BLUE force, RED force |
| Actions | Courses of action (COAs) |
| Payoff | MEF score differential |
| Equilibrium | Nash equilibrium via best-response self-play |
| Solution concept | Minimax (zero-sum game) |

**Best-Response Self-Play:** Both players iteratively compute their best response to the opponent's current strategy, converging toward Nash equilibrium.

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| gbc_score | Normalised BLUE advantage over RED: (blue_mef - red_mef + 1) / 2 |
| nash_gap | Deviation from zero-sum equilibrium: |blue + red - 1.0| |
| robustness_score | Minimum MEF across adversarial best-responses |
| coa_diversity | Mean pairwise Jaccard distance between COA action sets |

---

## Quickstart

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

```python
from coageneration.core import CourseOfAction, Force, GameState, SelfPlayEngine, compute_mef_score
from coageneration.evaluate import gbc_score, nash_gap

bluecoa = CourseOfAction(coa_id="b1", force=Force.BLUE, actions=[], objective="hold",
                         mef_score=compute_mef_score(0.8, 0.2, 0.1))
redcoa  = CourseOfAction(coa_id="r1", force=Force.RED,  actions=[], objective="attack",
                         mef_score=compute_mef_score(0.6, 0.3, 0.2))

print("GBC score:", gbc_score(bluecoa, redcoa))
print("Nash gap:", nash_gap(bluecoa.mef_score, redcoa.mef_score))
```

---

## Citation

```bibtex
@misc{anote2024coageneration,
  title  = {Adversarial Course-of-Action Generation: Game-Theoretic Multi-Agent Algorithms for MEF & GBC},
  author = {Anote AI},
  year   = {2024},
  url    = {https://github.com/anote-ai/research-coageneration}
}
```
