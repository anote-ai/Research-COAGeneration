"""Runnable baseline experiments (B0, B1, B4) over the existing coageneration
library, following the experimental design in
'research design document.md' (Section 7: Baseline Experiments).

This script produces REAL, measured numbers from the current random/greedy
self-play implementation in src/coageneration. It does NOT call any LLM
(no API key required), so it is runnable by anyone, deterministically,
without network access or credentials. The output of this exact script
(--seeds 30 --rounds 5) is checked into results/baselines_b0_b1_b4.json.

What this covers, mapped to "research design document.md":
  - B0: Random Valid COA (Section 7)
  - B1: Greedy MEF (Section 7)
  - B4: Random/heuristic self-play (Section 7) via SelfPlayEngine(policy=None)
  - Primary metric: held-out worst-case / 10th-percentile GBC score
    against a population of unseen random RED opponents (Section 10)

What this does NOT cover yet (explicitly out of scope for this script):
  - B2 Scripted Heuristic Planner (no scripted policy exists in src/ yet)
  - B3 LLM generation without self-play, and the proposed LLM-guided
    best-response self-play "test experiment" (Section 8) -- both require
    an ANTHROPIC_API_KEY and live model calls. See run_llm_policy.py for a
    thin runnable wrapper around the existing LLMPolicy class; it is not
    run automatically here because it costs money and is non-deterministic.
  - Held-out scenario/seed splitting (Section 6) -- this script reuses the
    same seed range for "training" and "evaluation" opponents. A real
    held-out split is future work (see Issue: Research Readiness Audit).

Usage:
    PYTHONPATH=src python3 experiments/run_baselines.py --seeds 30 --rounds 5
"""
from __future__ import annotations

import argparse
import json
import statistics
from typing import Dict, List

from coageneration.core import CourseOfAction, Force, SelfPlayEngine
from coageneration.data import make_coa, make_game_state
from coageneration.evaluate import (
    doctrinal_alignment_score,
    episode_summary,
    gbc_score,
    robustness_score,
)


def b0_random_valid_coa(seed: int) -> CourseOfAction:
    """B0: sample a COA uniformly at random (no opponent modelling)."""
    return make_coa(force=Force.BLUE, n_actions=3, seed=seed)


def b1_greedy_mef(seed: int, n_candidates: int = 8) -> CourseOfAction:
    """B1: generate n_candidates random COAs, keep the one with highest MEF."""
    candidates = [
        make_coa(force=Force.BLUE, n_actions=3, seed=seed * 1000 + i)
        for i in range(n_candidates)
    ]
    return max(candidates, key=lambda c: c.mef_score)


def b4_random_self_play(seed: int, rounds: int) -> Dict:
    """B4: iterative self-play using the built-in random best-response
    (i.e. the self-play structure without LLM guidance)."""
    state = make_game_state(seed=seed)
    engine = SelfPlayEngine(seed=seed)  # policy=None -> random best-response
    states = engine.run_episode(state, n_rounds=rounds)
    return episode_summary(states)


def evaluate_against_random_opponents(
    coa: CourseOfAction, seed: int, n_opponents: int = 10
) -> Dict[str, float]:
    """Score a single BLUE COA's robustness against a population of random
    RED opponents, per Section 10 (primary metric: held-out worst-case GBC).

    Note: these RED opponents are drawn from the same generator/seed space
    used elsewhere in this script, so this is NOT yet a true held-out split
    in the sense of Section 6. Treat these as a sanity-check population,
    not a rigorous held-out evaluation.
    """
    opponents = [
        make_coa(force=Force.RED, n_actions=3, seed=seed * 7919 + i)
        for i in range(n_opponents)
    ]
    gbc_scores = [gbc_score(coa, opp) for opp in opponents]
    gbc_scores_sorted = sorted(gbc_scores)
    p10_index = max(0, int(0.10 * len(gbc_scores_sorted)) - 1)
    return {
        "mean_gbc": statistics.mean(gbc_scores),
        "min_gbc": min(gbc_scores),
        "p10_gbc": gbc_scores_sorted[p10_index],
        "robustness_mef": robustness_score(coa, opponents),
        "doctrinal_alignment": doctrinal_alignment_score(coa),
    }


def run(n_seeds: int, n_rounds: int) -> Dict:
    results: Dict[str, List[Dict[str, float]]] = {"B0_random": [], "B1_greedy_mef": []}
    for seed in range(n_seeds):
        b0_coa = b0_random_valid_coa(seed)
        b1_coa = b1_greedy_mef(seed)
        results["B0_random"].append(evaluate_against_random_opponents(b0_coa, seed))
        results["B1_greedy_mef"].append(evaluate_against_random_opponents(b1_coa, seed))

    b4_summaries = [b4_random_self_play(seed, n_rounds) for seed in range(n_seeds)]
    blue_wins = sum(1 for s in b4_summaries if s["winner"] == "blue")

    def aggregate(rows: List[Dict[str, float]]) -> Dict[str, float]:
        keys = rows[0].keys()
        agg = {f"mean_{k}": statistics.mean(r[k] for r in rows) for k in keys}
        agg.update(
            {
                f"stdev_{k}": (statistics.stdev([r[k] for r in rows]) if len(rows) > 1 else 0.0)
                for k in keys
            }
        )
        return agg

    summary = {
        "config": {"n_seeds": n_seeds, "n_rounds": n_rounds},
        "B0_random": aggregate(results["B0_random"]),
        "B1_greedy_mef": aggregate(results["B1_greedy_mef"]),
        "B4_random_self_play": {
            "blue_win_rate": blue_wins / n_seeds,
            "n_episodes": n_seeds,
        },
        "note": (
            "All numbers in this file were computed by actually running "
            "experiments/run_baselines.py against the current random/greedy "
            "policies in src/coageneration. No LLM-guided policy (B3 / the "
            "proposed test experiment from the design docs) is included "
            "here because that requires an ANTHROPIC_API_KEY and live API "
            "calls. See run_llm_policy.py and results/README.md."
        ),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run B0/B1/B4 baselines")
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    summary = run(args.seeds, args.rounds)
    text = json.dumps(summary, indent=2, sort_keys=False)
    print(text)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)


if __name__ == "__main__":
    main()
