#!/usr/bin/env python3
"""Experiment 0: Baseline comparison (B0 random, B1 greedy-MEF, B2 scripted heuristic,
B3 one-shot LLM-free random-policy self-play) on synthetic scenarios.

This is a REAL, runnable experiment over the synthetic scenario corpus already
defined in coageneration.data. It does NOT call any LLM API (no network access
required) so it can run in CI. It measures GBC score, robustness (worst-case
MEF across repeated adversarial draws), and action diversity for each baseline,
and writes results to results/exp0_baselines.json.

This corresponds to the "Baseline Experiments" (B0-B2) section of
`research design document.md`. B3 (LLM-guided self-play) is stubbed here
because it requires ANTHROPIC_API_KEY; see results/exp0_baselines.json field
"b3_llm_self_play" which is explicitly marked as not executed.

Usage:
    python experiments/exp0_baselines.py
"""

from __future__ import annotations

import json
import os
import random
import statistics
import sys
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from coageneration.core import Action, ActionCategory, CourseOfAction, Force, SelfPlayEngine, build_chain, compute_mef_score
from coageneration.data import make_coa, make_game_state, make_scenario_corpus
from coageneration.evaluate import coa_diversity, doctrinal_alignment_score, gbc_score, robustness_score

N_SEEDS = 30  # matches DESIGN_DOC's "at least 30 independent seeds" recommendation
N_ROUNDS = 5


def b0_random_coa(seed: int, force: Force = Force.BLUE) -> CourseOfAction:
    """B0: sample a valid COA uniformly at random."""
    return make_coa(force=force, n_actions=random.Random(seed).randint(2, 5), seed=seed)


def b1_greedy_mef(seed: int, n_candidates: int = 8, force: Force = Force.BLUE) -> CourseOfAction:
    """B1: generate candidates, keep the highest-MEF one (no opponent model)."""
    candidates = [make_coa(force=force, seed=seed * 100 + i) for i in range(n_candidates)]
    return max(candidates, key=lambda c: c.mef_score)


def b2_scripted_heuristic(seed: int, force: Force = Force.BLUE) -> CourseOfAction:
    """B2: fixed observe -> prepare -> act -> recover sequence."""
    rng = random.Random(seed)
    plan = ["recon", "assess_supply_levels", "attack", "withdraw"]
    categories = [
        ActionCategory.INTELLIGENCE,
        ActionCategory.LOGISTICS,
        ActionCategory.KINETIC,
        ActionCategory.LOGISTICS,
    ]
    actions = [
        Action(
            action_type=plan[i],
            category=categories[i],
            asset_id=f"asset-{i:03d}",
            priority=i + 1,
            expected_duration_s=rng.uniform(30, 300),
        )
        for i in range(len(plan))
    ]
    mef = compute_mef_score(
        effectiveness=rng.uniform(0.45, 0.65),
        cost=rng.uniform(0.2, 0.4),
        risk=rng.uniform(0.1, 0.3),
    )
    return CourseOfAction(
        force=force,
        actions=actions,
        chain=build_chain(actions),
        objective="scripted observe-prepare-act-recover",
        mef_score=mef,
    )


def evaluate_baseline(name: str, generator, n_seeds: int = N_SEEDS) -> Dict:
    """Run a baseline generator across seeds, score against random RED best-responses."""
    engine = SelfPlayEngine(seed=0)
    gbc_scores: List[float] = []
    worst_case_mefs: List[float] = []
    doctrinal_scores: List[float] = []
    coas: List[CourseOfAction] = []

    for seed in range(n_seeds):
        state = make_game_state(seed=seed)
        blue_coa = generator(seed)
        coas.append(blue_coa)

        # Evaluate against 5 independently-sampled RED responses (held-out adversary draws)
        red_responses = [engine.best_response(blue_coa, state) for _ in range(5)]
        gbc_scores.append(statistics.mean(gbc_score(blue_coa, r) for r in red_responses))
        worst_case_mefs.append(robustness_score(blue_coa, red_responses))
        doctrinal_scores.append(doctrinal_alignment_score(blue_coa))

    return {
        "name": name,
        "n_seeds": n_seeds,
        "mean_gbc": round(statistics.mean(gbc_scores), 4),
        "stdev_gbc": round(statistics.stdev(gbc_scores), 4) if n_seeds > 1 else 0.0,
        "p10_worst_case_mef": round(sorted(worst_case_mefs)[max(0, n_seeds // 10 - 1)], 4),
        "min_worst_case_mef": round(min(worst_case_mefs), 4),
        "mean_doctrinal_alignment": round(statistics.mean(doctrinal_scores), 4),
        "action_diversity_jaccard": round(coa_diversity(coas), 4),
    }


def main() -> None:
    random.seed(0)
    results = {
        "experiment": "exp0_baselines",
        "description": (
            "Real, locally-computed comparison of B0 (random), B1 (greedy MEF), "
            "and B2 (scripted heuristic) baselines against randomly-sampled RED "
            "best-responses, using the synthetic scenario generators in "
            "coageneration.data. No LLM calls were made for this run."
        ),
        "n_seeds": N_SEEDS,
        "baselines": [
            evaluate_baseline("B0_random", b0_random_coa),
            evaluate_baseline("B1_greedy_mef", b1_greedy_mef),
            evaluate_baseline("B2_scripted_heuristic", b2_scripted_heuristic),
        ],
        "b3_llm_self_play": {
            "status": "NOT EXECUTED",
            "reason": (
                "Requires ANTHROPIC_API_KEY and network access; not run in this "
                "session. Run `python scripts/run_demo.py --llm` and "
                "`pytest tests/test_llm_policy.py` manually, then extend this "
                "script with a real B3/B4 + LLM-guided self-play comparison."
            ),
        },
        "scenario_corpus_smoke_test": {
            "n_scenario_cases": len(make_scenario_corpus()),
            "note": "make_scenario_corpus() produces urban/maritime/multi-domain cases; not yet wired into this experiment's main loop.",
        },
    }

    out_dir = Path(__file__).resolve().parent.parent / "results"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "exp0_baselines.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote {out_path}")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
