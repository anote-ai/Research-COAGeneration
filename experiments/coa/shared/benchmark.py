#!/usr/bin/env python3
"""COA-Bench experiment: reuses existing coageneration library code only.

No new metrics or generation logic — this script just calls the existing
self-play engine, policies, scenario factories, and evaluation functions in a
loop and prints aggregated, bootstrap-CI'd results.

Usage:
    python experiments/coa/dai2026/run_benchmark.py
    python experiments/coa/aaai2027/run_benchmark.py
    python experiments/coa/shared/benchmark.py --output results/coa/aaai2027/main
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from coageneration import (
    DoctrineAwareBestResponsePolicy,
    MultiAgentCouncilPolicy,
    SampledBestResponsePolicy,
    SelfPlayEngine,
    advantage_score,
    battlecoa_validity_vector,
    bootstrap_ci,
    compare_coas,
    compare_selection_tradeoff,
    council_diagnostics,
    doctrinal_alignment_score,
    framing_sensitivity_delta,
    lanchester_wargame_outcome,
    nash_gap,
)
from coageneration.data import (
    make_air_defense_operations_case,
    make_humanitarian_evacuation_case,
    make_maritime_operations_case,
    make_multi_domain_operations_case,
    make_scenario_corpus,
    make_urban_operations_case,
)

N_SEEDS = 10  # 10 base seeds x 5 templates = 50 scenarios
N_SAMPLES = 8  # candidates per SampledBestResponsePolicy call
RESPONSE_BUDGETS = [1, 2, 4, 8, 16]


def to_payoff(quality_score: float) -> float:
    """Rescale a [-1, 1] quality score to a [0, 1] payoff."""
    return (quality_score + 1.0) / 2.0


def main(
    default_output: Path | None = None,
    venue: str = "shared",
    source_script: str = "experiments/coa/shared/benchmark.py",
) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=default_output or Path("results/coa/shared/main"),
        help="Directory for generated COA benchmark artifacts.",
    )
    args = parser.parse_args()

    rows = []
    budget_rows = []
    council_rows = []
    for i in range(N_SEEDS):
        base_seed = 100 + i * 3
        for case in make_scenario_corpus(seed=base_seed):
            blue_coa = case.seed_coas[0]
            state = case.game_state

            red_single = SelfPlayEngine(seed=base_seed).best_response(blue_coa, state)

            policy = SampledBestResponsePolicy(n_samples=N_SAMPLES, seed=base_seed)
            candidates = policy.generate_candidates(state, blue_coa)
            red_sampled = max(candidates, key=lambda c: c.quality_score)
            comparison = compare_coas(candidates)
            tradeoff = compare_selection_tradeoff(candidates)

            doctrine_policy = DoctrineAwareBestResponsePolicy(
                n_samples=N_SAMPLES,
                seed=base_seed,
                quality_weight=0.7,
                doctrine_weight=0.3,
            )
            red_doctrine_aware = doctrine_policy.generate_coa(state, blue_coa)

            wargame_single = lanchester_wargame_outcome(state, blue_coa, red_single)
            wargame_sampled = lanchester_wargame_outcome(state, blue_coa, red_sampled)
            wargame_doctrine = lanchester_wargame_outcome(
                state, blue_coa, red_doctrine_aware
            )

            council = MultiAgentCouncilPolicy(
                red_team_samples=4,
                seed=base_seed,
            ).run_council(state, case.seed_coas)
            council_stats = council_diagnostics(council)
            council_wargame = lanchester_wargame_outcome(
                state, council.selected_blue, council.selected_red
            )
            blue_battlecoa = battlecoa_validity_vector(blue_coa)
            council_battlecoa = battlecoa_validity_vector(council.selected_blue)

            rows.append(
                {
                    "scenario_id": case.profile.scenario_id,
                    "terrain_type": case.profile.terrain_type,
                    "framing": case.profile.framing,
                    "advantage_single": advantage_score(blue_coa, red_single),
                    "advantage_sampled": advantage_score(blue_coa, red_sampled),
                    "advantage_doctrine_aware": advantage_score(
                        blue_coa, red_doctrine_aware
                    ),
                    "nash_gap_single": nash_gap(
                        to_payoff(blue_coa.quality_score), to_payoff(red_single.quality_score)
                    ),
                    "nash_gap_sampled": nash_gap(
                        to_payoff(blue_coa.quality_score), to_payoff(red_sampled.quality_score)
                    ),
                    "nash_gap_doctrine_aware": nash_gap(
                        to_payoff(blue_coa.quality_score),
                        to_payoff(red_doctrine_aware.quality_score),
                    ),
                    "blue_doctrinal_alignment": doctrinal_alignment_score(blue_coa),
                    "blue_path_optionality": blue_battlecoa["path_optionality"],
                    "blue_vertex_parsimony": blue_battlecoa["vertex_parsimony"],
                    "blue_worldline_completion": blue_battlecoa[
                        "worldline_completion"
                    ],
                    "red_doctrinal_alignment_single": doctrinal_alignment_score(red_single),
                    "red_doctrinal_alignment_sampled": doctrinal_alignment_score(red_sampled),
                    "red_doctrinal_alignment_doctrine_aware": doctrinal_alignment_score(
                        red_doctrine_aware
                    ),
                    "candidate_diversity": comparison.diversity,
                    "candidate_quality_spread": comparison.quality_spread,
                    "n_pareto_optimal": len(comparison.pareto_optimal_ids),
                    "selection_quality_regret": tradeoff.quality_regret,
                    "selection_doctrinal_gain": tradeoff.doctrinal_gain,
                    "selection_changed": tradeoff.quality_best_id
                    != tradeoff.composite_best_id,
                    "blue_wins_single": wargame_single["winner"] == "blue",
                    "blue_wins_sampled": wargame_sampled["winner"] == "blue",
                    "blue_wins_doctrine_aware": wargame_doctrine["winner"] == "blue",
                    "advantage_council": council_stats.selected_advantage,
                    "blue_wins_council": council_wargame["winner"] == "blue",
                    "council_diversity": council_stats.council_diversity,
                    "council_revised_diversity": council_stats.revised_diversity,
                    "council_consensus_gap": council_stats.consensus_gap,
                    "council_adversarial_pressure": council_stats.adversarial_pressure,
                    "council_robustness_margin": council_stats.robustness_margin,
                    "council_pressure_reduction": council_stats.pressure_reduction,
                    "council_selected_round": council.round_index[
                        council.selected_blue.coa_id
                    ],
                    "council_path_optionality": council_battlecoa[
                        "path_optionality"
                    ],
                    "council_vertex_parsimony": council_battlecoa[
                        "vertex_parsimony"
                    ],
                    "council_worldline_completion": council_battlecoa[
                        "worldline_completion"
                    ],
                }
            )

            council_rows.append(
                {
                    "scenario_id": case.profile.scenario_id,
                    "terrain_type": case.profile.terrain_type,
                    "selected_blue_id": council.selected_blue.coa_id,
                    "selected_red_id": council.selected_red.coa_id,
                    "selected_advantage": council_stats.selected_advantage,
                    "blue_doctrinal_alignment": doctrinal_alignment_score(
                        council.selected_blue
                    ),
                    "red_doctrinal_alignment": doctrinal_alignment_score(
                        council.selected_red
                    ),
                    "path_optionality": council_battlecoa["path_optionality"],
                    "vertex_parsimony": council_battlecoa["vertex_parsimony"],
                    "worldline_completion": council_battlecoa[
                        "worldline_completion"
                    ],
                    "council_diversity": council_stats.council_diversity,
                    "revised_diversity": council_stats.revised_diversity,
                    "consensus_gap": council_stats.consensus_gap,
                    "adversarial_pressure": council_stats.adversarial_pressure,
                    "robustness_margin": council_stats.robustness_margin,
                    "pressure_reduction": council_stats.pressure_reduction,
                    "n_blue_candidates": len(council.blue_candidates),
                    "n_revised_candidates": len(council.revised_candidates),
                    "selected_round": council.round_index[
                        council.selected_blue.coa_id
                    ],
                    "blue_wins": council_wargame["winner"] == "blue",
                }
            )

            for budget in RESPONSE_BUDGETS:
                budget_policy = SampledBestResponsePolicy(
                    n_samples=budget, seed=base_seed
                )
                budget_candidates = budget_policy.generate_candidates(state, blue_coa)
                budget_best = max(budget_candidates, key=lambda c: c.quality_score)
                budget_comparison = compare_coas(budget_candidates)
                budget_rows.append(
                    {
                        "scenario_id": case.profile.scenario_id,
                        "terrain_type": case.profile.terrain_type,
                        "response_budget": budget,
                        "advantage": advantage_score(blue_coa, budget_best),
                        "red_quality": budget_best.quality_score,
                        "red_doctrinal_alignment": doctrinal_alignment_score(
                            budget_best
                        ),
                        "candidate_diversity": budget_comparison.diversity,
                        "candidate_quality_spread": budget_comparison.quality_spread,
                        "n_pareto_optimal": len(
                            budget_comparison.pareto_optimal_ids
                        ),
                    }
                )

    def boot(key: str):
        return bootstrap_ci(
            lambda sample: mean(r[key] for r in sample), rows, n_boot=1000, seed=0
        )

    print(f"COA-Bench experiment: {len(rows)} scenarios "
          f"({N_SEEDS} seeds x 5 templates), {N_SAMPLES} candidates/sample\n")

    print("== Best-response comparison: single random sample vs. sampled-best-response ==")
    print(f"Advantage score (single):    {boot('advantage_single')}")
    print(f"Advantage score (sampled):   {boot('advantage_sampled')}")
    print(f"Nash gap (single):  {boot('nash_gap_single')}")
    print(f"Nash gap (sampled): {boot('nash_gap_sampled')}")
    print(f"Advantage score (doctrine-aware): {boot('advantage_doctrine_aware')}")
    print(f"Nash gap (doctrine-aware):        {boot('nash_gap_doctrine_aware')}")

    print("\n== Doctrinal alignment: does quality-greedy selection cost doctrinal coherence? ==")
    print(f"Blue (fixed):              {boot('blue_doctrinal_alignment')}")
    print(f"Red, single-sample:        {boot('red_doctrinal_alignment_single')}")
    print(f"Red, sampled-best-response: {boot('red_doctrinal_alignment_sampled')}")
    print(
        "Red, doctrine-aware response: "
        f"{boot('red_doctrinal_alignment_doctrine_aware')}"
    )

    print("\n== BattleCOA-inspired validity proxies for BLUE COAs ==")
    print(f"Seed path optionality:      {boot('blue_path_optionality')}")
    print(f"Seed vertex parsimony:      {boot('blue_vertex_parsimony')}")
    print(f"Seed worldline completion:  {boot('blue_worldline_completion')}")
    print(f"Council path optionality:   {boot('council_path_optionality')}")
    print(f"Council vertex parsimony:   {boot('council_vertex_parsimony')}")
    print(f"Council worldline completion:{boot('council_worldline_completion')}")

    print("\n== Multi-COA comparison (compare_coas over the 8 sampled candidates) ==")
    print(f"Candidate diversity:    {boot('candidate_diversity')}")
    print(f"Candidate quality spread:   {boot('candidate_quality_spread')}")
    print(f"Pareto-optimal count:   {boot('n_pareto_optimal')}")
    print(f"Selection quality regret: {boot('selection_quality_regret')}")
    print(f"Selection doctrinal gain: {boot('selection_doctrinal_gain')}")
    print(f"Selection changed rate:  {mean(r['selection_changed'] for r in rows):.3f}")

    blue_win_rate_single = mean(r["blue_wins_single"] for r in rows)
    blue_win_rate_sampled = mean(r["blue_wins_sampled"] for r in rows)
    print("\n== Lanchester wargame outcome: BLUE win rate ==")
    print(f"vs. single-sample RED:        {blue_win_rate_single:.3f}")
    print(f"vs. sampled-best-response RED: {blue_win_rate_sampled:.3f}")
    blue_win_rate_doctrine = mean(r["blue_wins_doctrine_aware"] for r in rows)
    print(f"vs. doctrine-aware RED:        {blue_win_rate_doctrine:.3f}")
    blue_win_rate_council = mean(r["blue_wins_council"] for r in rows)
    print(f"multi-agent council BLUE:      {blue_win_rate_council:.3f}")

    print("\n== Multi-agent council algorithm ==")
    print(f"Council advantage:          {boot('advantage_council')}")
    print(f"Council candidate diversity: {boot('council_diversity')}")
    print(f"Council revised diversity:   {boot('council_revised_diversity')}")
    print(f"Council consensus gap:       {boot('council_consensus_gap')}")
    print(f"Council adversarial pressure:{boot('council_adversarial_pressure')}")
    print(f"Council robustness margin:   {boot('council_robustness_margin')}")
    print(f"Council pressure reduction:  {boot('council_pressure_reduction')}")
    print(
        "Council selected revised candidate rate: "
        f"{mean(r['council_selected_round'] for r in rows):.3f}"
    )

    print("\n== Response budget curve: sampled-best-response strength ==")
    for budget in RESPONSE_BUDGETS:
        subset = [r for r in budget_rows if r["response_budget"] == budget]
        result = bootstrap_ci(
            lambda sample: mean(r["advantage"] for r in sample),
            subset,
            n_boot=1000,
            seed=0,
        )
        print(f"Budget {budget:>2}: advantage {result}")

    print("\n== Scenario framing sensitivity (doctrinal alignment, blue/neutral/adversary) ==")
    framing_deltas = []
    for i in range(N_SEEDS):
        seed = 200 + i
        for factory in (
            make_urban_operations_case,
            make_maritime_operations_case,
            make_multi_domain_operations_case,
            make_air_defense_operations_case,
            make_humanitarian_evacuation_case,
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

    output = args.output
    output.mkdir(parents=True, exist_ok=True)

    with open(output / "rows.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    with open(output / "budget_curve.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(budget_rows[0].keys()))
        writer.writeheader()
        writer.writerows(budget_rows)

    with open(output / "council_rows.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(council_rows[0].keys()))
        writer.writeheader()
        writer.writerows(council_rows)

    terrain_rows = []
    by_terrain = defaultdict(list)
    for row in rows:
        by_terrain[row["terrain_type"]].append(row)
    for terrain, terrain_data in sorted(by_terrain.items()):
        terrain_rows.append(
            {
                "terrain_type": terrain,
                "n_scenarios": len(terrain_data),
                "advantage_single": mean(r["advantage_single"] for r in terrain_data),
                "advantage_sampled": mean(r["advantage_sampled"] for r in terrain_data),
                "advantage_doctrine_aware": mean(
                    r["advantage_doctrine_aware"] for r in terrain_data
                ),
                "blue_win_rate_single": mean(
                    r["blue_wins_single"] for r in terrain_data
                ),
                "blue_win_rate_sampled": mean(
                    r["blue_wins_sampled"] for r in terrain_data
                ),
                "blue_win_rate_doctrine_aware": mean(
                    r["blue_wins_doctrine_aware"] for r in terrain_data
                ),
                "blue_win_rate_council": mean(
                    r["blue_wins_council"] for r in terrain_data
                ),
                "selection_changed_rate": mean(
                    r["selection_changed"] for r in terrain_data
                ),
                "candidate_diversity": mean(
                    r["candidate_diversity"] for r in terrain_data
                ),
                "council_diversity": mean(
                    r["council_diversity"] for r in terrain_data
                ),
                "council_revised_selection_rate": mean(
                    r["council_selected_round"] for r in terrain_data
                ),
            }
        )
    with open(output / "terrain_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(terrain_rows[0].keys()))
        writer.writeheader()
        writer.writerows(terrain_rows)

    summary_metrics = {
        "advantage_single": boot("advantage_single"),
        "advantage_sampled": boot("advantage_sampled"),
        "advantage_doctrine_aware": boot("advantage_doctrine_aware"),
        "nash_gap_single": boot("nash_gap_single"),
        "nash_gap_sampled": boot("nash_gap_sampled"),
        "nash_gap_doctrine_aware": boot("nash_gap_doctrine_aware"),
        "blue_doctrinal_alignment": boot("blue_doctrinal_alignment"),
        "blue_path_optionality": boot("blue_path_optionality"),
        "blue_vertex_parsimony": boot("blue_vertex_parsimony"),
        "blue_worldline_completion": boot("blue_worldline_completion"),
        "red_doctrinal_alignment_single": boot("red_doctrinal_alignment_single"),
        "red_doctrinal_alignment_sampled": boot("red_doctrinal_alignment_sampled"),
        "red_doctrinal_alignment_doctrine_aware": boot(
            "red_doctrinal_alignment_doctrine_aware"
        ),
        "candidate_diversity": boot("candidate_diversity"),
        "candidate_quality_spread": boot("candidate_quality_spread"),
        "n_pareto_optimal": boot("n_pareto_optimal"),
        "selection_quality_regret": boot("selection_quality_regret"),
        "selection_doctrinal_gain": boot("selection_doctrinal_gain"),
        "advantage_council": boot("advantage_council"),
        "council_diversity": boot("council_diversity"),
        "council_revised_diversity": boot("council_revised_diversity"),
        "council_consensus_gap": boot("council_consensus_gap"),
        "council_adversarial_pressure": boot("council_adversarial_pressure"),
        "council_robustness_margin": boot("council_robustness_margin"),
        "council_pressure_reduction": boot("council_pressure_reduction"),
        "council_path_optionality": boot("council_path_optionality"),
        "council_vertex_parsimony": boot("council_vertex_parsimony"),
        "council_worldline_completion": boot("council_worldline_completion"),
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
        "response_budgets": RESPONSE_BUDGETS,
        "blue_win_rate_single": blue_win_rate_single,
        "blue_win_rate_sampled": blue_win_rate_sampled,
        "blue_win_rate_doctrine_aware": blue_win_rate_doctrine,
        "blue_win_rate_council": blue_win_rate_council,
        "selection_changed_rate": mean(r["selection_changed"] for r in rows),
        "multi_agent_council": {
            "blue_proposer_agents": 5,
            "red_team_samples_per_candidate": 4,
            "deliberation_width": 2,
            "revision_bonus": 0.025,
            "selected_revised_candidate_rate": mean(
                r["council_selected_round"] for r in rows
            ),
            "selection_objective": "0.45 quality + 0.25 doctrine + 0.10 diversity - 0.20 adversarial pressure",
        },
        "venue": venue,
        "source": f"{source_script} — outcomes from the coageneration self-play "
        "simulator, not a production deployment or live LLM.",
    }
    with open(output / "details.json", "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2)

    print(f"\nResults written to {output}/")


if __name__ == "__main__":
    main()
