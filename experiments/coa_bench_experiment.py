#!/usr/bin/env python3
"""COA-Bench experiment: reuses existing coageneration library code only.

No new metrics or generation logic — this script just calls the existing
self-play engine, policies, scenario factories, and evaluation functions in a
loop and prints aggregated, bootstrap-CI'd results.

Usage:
    python experiments/coa_bench_experiment.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from statistics import mean

from coageneration import (
    SampledBestResponsePolicy,
    SelfPlayEngine,
    bootstrap_ci,
    compare_coas,
    doctrinal_alignment_score,
    framing_sensitivity_delta,
    gbc_score,
    lanchester_wargame_outcome,
    nash_gap,
)
from coageneration.data import (
    make_maritime_operations_case,
    make_multi_domain_operations_case,
    make_scenario_corpus,
    make_urban_operations_case,
)

N_SEEDS = 10  # 10 base seeds x 3 templates (urban/maritime/multi-domain) = 30 scenarios
N_SAMPLES = 8  # candidates per SampledBestResponsePolicy call


def to_payoff(mef_score: float) -> float:
    """Rescale a [-1, 1] MEF score to a [0, 1] payoff for nash_gap."""
    return (mef_score + 1.0) / 2.0


def main() -> None:
    rows = []
    for i in range(N_SEEDS):
        base_seed = 100 + i * 3
        for case in make_scenario_corpus(seed=base_seed):
            blue_coa = case.seed_coas[0]
            state = case.game_state

            red_single = SelfPlayEngine(seed=base_seed).best_response(blue_coa, state)

            policy = SampledBestResponsePolicy(n_samples=N_SAMPLES, seed=base_seed)
            candidates = policy.generate_candidates(state, blue_coa)
            red_sampled = max(candidates, key=lambda c: c.mef_score)
            comparison = compare_coas(candidates)

            wargame_single = lanchester_wargame_outcome(state, blue_coa, red_single)
            wargame_sampled = lanchester_wargame_outcome(state, blue_coa, red_sampled)

            rows.append(
                {
                    "scenario_id": case.profile.scenario_id,
                    "gbc_single": gbc_score(blue_coa, red_single),
                    "gbc_sampled": gbc_score(blue_coa, red_sampled),
                    "nash_gap_single": nash_gap(
                        to_payoff(blue_coa.mef_score), to_payoff(red_single.mef_score)
                    ),
                    "nash_gap_sampled": nash_gap(
                        to_payoff(blue_coa.mef_score), to_payoff(red_sampled.mef_score)
                    ),
                    "blue_doctrinal_alignment": doctrinal_alignment_score(blue_coa),
                    "red_doctrinal_alignment_single": doctrinal_alignment_score(red_single),
                    "red_doctrinal_alignment_sampled": doctrinal_alignment_score(red_sampled),
                    "candidate_diversity": comparison.diversity,
                    "candidate_mef_spread": comparison.mef_spread,
                    "n_pareto_optimal": len(comparison.pareto_optimal_ids),
                    "blue_wins_single": wargame_single["winner"] == "blue",
                    "blue_wins_sampled": wargame_sampled["winner"] == "blue",
                }
            )

    def boot(key: str):
        return bootstrap_ci(
            lambda sample: mean(r[key] for r in sample), rows, n_boot=1000, seed=0
        )

    print(f"COA-Bench experiment: {len(rows)} scenarios "
          f"({N_SEEDS} seeds x 3 templates), {N_SAMPLES} candidates/sample\n")

    print("== Best-response comparison: single random sample vs. sampled-best-response ==")
    print(f"GBC (single):    {boot('gbc_single')}")
    print(f"GBC (sampled):   {boot('gbc_sampled')}")
    print(f"Nash gap (single):  {boot('nash_gap_single')}")
    print(f"Nash gap (sampled): {boot('nash_gap_sampled')}")

    print("\n== Doctrinal alignment: does MEF-greedy selection cost doctrinal coherence? ==")
    print(f"Blue (fixed):              {boot('blue_doctrinal_alignment')}")
    print(f"Red, single-sample:        {boot('red_doctrinal_alignment_single')}")
    print(f"Red, sampled-best-response: {boot('red_doctrinal_alignment_sampled')}")

    print("\n== Multi-COA comparison (compare_coas over the 8 sampled candidates) ==")
    print(f"Candidate diversity:    {boot('candidate_diversity')}")
    print(f"Candidate MEF spread:   {boot('candidate_mef_spread')}")
    print(f"Pareto-optimal count:   {boot('n_pareto_optimal')}")

    blue_win_rate_single = mean(r["blue_wins_single"] for r in rows)
    blue_win_rate_sampled = mean(r["blue_wins_sampled"] for r in rows)
    print("\n== Lanchester wargame outcome: BLUE win rate ==")
    print(f"vs. single-sample RED:        {blue_win_rate_single:.3f}")
    print(f"vs. sampled-best-response RED: {blue_win_rate_sampled:.3f}")

    print("\n== Scenario framing sensitivity (doctrinal alignment, blue/neutral/adversary) ==")
    framing_deltas = []
    for i in range(N_SEEDS):
        seed = 200 + i
        for factory in (
            make_urban_operations_case,
            make_maritime_operations_case,
            make_multi_domain_operations_case,
        ):
            scores = {
                framing: doctrinal_alignment_score(
                    factory(seed=seed, framing=framing).seed_coas[0]
                )
                for framing in ("blue", "neutral", "adversary")
            }
            framing_deltas.append(framing_sensitivity_delta(scores))
    delta_result = bootstrap_ci(
        lambda sample: mean(sample), framing_deltas, n_boot=1000, seed=0
    )
    print(f"Framing sensitivity delta: {delta_result}")

    output = Path("results/coa-bench/main")
    output.mkdir(parents=True, exist_ok=True)

    with open(output / "rows.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summary_metrics = {
        "gbc_single": boot("gbc_single"),
        "gbc_sampled": boot("gbc_sampled"),
        "nash_gap_single": boot("nash_gap_single"),
        "nash_gap_sampled": boot("nash_gap_sampled"),
        "blue_doctrinal_alignment": boot("blue_doctrinal_alignment"),
        "red_doctrinal_alignment_single": boot("red_doctrinal_alignment_single"),
        "red_doctrinal_alignment_sampled": boot("red_doctrinal_alignment_sampled"),
        "candidate_diversity": boot("candidate_diversity"),
        "candidate_mef_spread": boot("candidate_mef_spread"),
        "n_pareto_optimal": boot("n_pareto_optimal"),
        "framing_sensitivity_delta": delta_result,
    }
    with open(output / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "mean", "ci_lower", "ci_upper", "n_boot", "confidence"])
        for name, result in summary_metrics.items():
            writer.writerow(
                [name, result.mean, result.lower, result.upper, result.n_boot, result.confidence]
            )

    details = {
        "n_scenarios": len(rows),
        "n_seeds": N_SEEDS,
        "n_samples": N_SAMPLES,
        "blue_win_rate_single": blue_win_rate_single,
        "blue_win_rate_sampled": blue_win_rate_sampled,
        "source": "experiments/coa_bench_experiment.py — outcomes from the coageneration "
        "self-play simulator, not a production deployment or live LLM.",
    }
    with open(output / "details.json", "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2)

    print(f"\nResults written to {output}/")


if __name__ == "__main__":
    main()
