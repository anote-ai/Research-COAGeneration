#!/usr/bin/env python3
"""COA-Bench experiment: reuses existing coageneration library code only.

Compares three RED response policies across 90 synthetic scenarios:
  - single:   one random best-response (SelfPlayEngine)
  - sampled:  best of N_SAMPLES random candidates (SampledBestResponsePolicy)
  - llm:      Claude-backed strategic response (LLMPolicy)

LLMPolicy requires ANTHROPIC_API_KEY in the environment. If not set, that
column is skipped and a warning is printed.

Usage:
    python experiments/coa_bench_experiment.py
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path
from statistics import mean

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from coageneration import (
    LLMPolicy,
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

N_SEEDS = 30   # 30 seeds x 3 templates = 90 scenarios
N_SAMPLES = 8  # candidates per SampledBestResponsePolicy call


def to_payoff(mef_score: float) -> float:
    return (mef_score + 1.0) / 2.0


def _init_llm_policy() -> LLMPolicy | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("WARNING: ANTHROPIC_API_KEY not set — skipping LLMPolicy column.", file=sys.stderr)
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        return LLMPolicy(client=client, model="claude-haiku-4-5-20251001", max_tokens=512)
    except Exception as e:
        print(f"WARNING: could not initialise LLMPolicy ({e}) — skipping.", file=sys.stderr)
        return None


def _safe_llm_generate(policy: LLMPolicy, state, blue_coa):
    try:
        return policy.generate_coa(state, blue_coa)
    except Exception as e:
        print(f"  LLM error: {e} — using fallback", file=sys.stderr)
        return SelfPlayEngine(seed=0).best_response(blue_coa, state)


def _save_figures(rows: list) -> None:
    figures_dir = Path("papers/coa-bench/figures")
    figures_dir.mkdir(parents=True, exist_ok=True)

    has_llm = any(r.get("gbc_llm") is not None for r in rows)
    policies = ["single", "sampled"] + (["llm"] if has_llm else [])
    labels = {"single": "Random single", "sampled": f"Sampled best-of-{N_SAMPLES}", "llm": "LLM (Claude)"}
    colors = {"single": "#6baed6", "sampled": "#2171b5", "llm": "#084594"}

    metrics = [
        ("gbc", "GBC score (BLUE advantage)", [0.3, 0.7]),
        ("nash_gap", "Nash gap", [0.0, 0.5]),
        ("red_doctrinal_alignment", "RED doctrinal alignment", [0.4, 0.9]),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (key, ylabel, ylim) in zip(axes, metrics):
        for i, policy in enumerate(policies):
            col = f"{key}_{policy}"
            vals = [r[col] for r in rows if r.get(col) is not None]
            result = bootstrap_ci(lambda s: mean(s), vals, n_boot=1000, seed=0)
            x = i
            ax.bar(x, result.mean, color=colors[policy], width=0.5, label=labels[policy])
            ax.errorbar(x, result.mean, yerr=[[result.mean - result.lower], [result.upper - result.mean]],
                        fmt="none", color="black", capsize=4)
        ax.set_ylabel(ylabel)
        ax.set_ylim(ylim)
        ax.set_xticks(range(len(policies)))
        ax.set_xticklabels([labels[p] for p in policies], rotation=15, ha="right", fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    fig.suptitle("COA-Bench: RED policy comparison (90 scenarios, 95% CI)", fontsize=11)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(figures_dir / f"policy_comparison.{ext}", bbox_inches="tight", dpi=150)
    plt.close(fig)

    # Pareto frontier figure
    fig2, ax2 = plt.subplots(figsize=(5, 4))
    sample_rows = rows[:10]
    for row_idx, row in enumerate(sample_rows):
        mef_col = f"candidate_mef_values_{row_idx}"
        da_col = f"candidate_da_values_{row_idx}"
        if mef_col in row and da_col in row:
            mef_vals = json.loads(row[mef_col])
            da_vals = json.loads(row[da_col])
            ax2.scatter(mef_vals, da_vals, alpha=0.4, s=20, color="#2171b5")

    ax2.set_xlabel("MEF score")
    ax2.set_ylabel("Doctrinal alignment")
    ax2.set_title(f"Candidate COA scatter (first 10 scenarios, {N_SAMPLES} candidates each)")
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    fig2.tight_layout()
    for ext in ("pdf", "png"):
        fig2.savefig(figures_dir / f"pareto_scatter.{ext}", bbox_inches="tight", dpi=150)
    plt.close(fig2)

    print(f"Figures saved to {figures_dir}/")


def main() -> None:
    llm_policy = _init_llm_policy()
    has_llm = llm_policy is not None

    rows = []
    print(f"COA-Bench: {N_SEEDS * 3} scenarios ({N_SEEDS} seeds x 3 templates), "
          f"{N_SAMPLES} candidates/sample, LLM={'yes' if has_llm else 'no'}\n")

    for i in range(N_SEEDS):
        base_seed = 100 + i * 3
        for case in make_scenario_corpus(seed=base_seed):
            blue_coa = case.seed_coas[0]
            state = case.game_state

            # Policy 1: single random
            red_single = SelfPlayEngine(seed=base_seed).best_response(blue_coa, state)

            # Policy 2: sampled best-of-N
            policy = SampledBestResponsePolicy(n_samples=N_SAMPLES, seed=base_seed)
            candidates = policy.generate_candidates(state, blue_coa)
            red_sampled = max(candidates, key=lambda c: c.mef_score)
            comparison = compare_coas(candidates)

            # Policy 3: LLM (optional)
            red_llm = _safe_llm_generate(llm_policy, state, blue_coa) if has_llm else None

            wargame_single = lanchester_wargame_outcome(state, blue_coa, red_single)
            wargame_sampled = lanchester_wargame_outcome(state, blue_coa, red_sampled)
            wargame_llm = lanchester_wargame_outcome(state, blue_coa, red_llm) if red_llm else None

            row_idx = len(rows)
            row = {
                "scenario_id": case.profile.scenario_id,
                "gbc_single": gbc_score(blue_coa, red_single),
                "gbc_sampled": gbc_score(blue_coa, red_sampled),
                "nash_gap_single": nash_gap(to_payoff(blue_coa.mef_score), to_payoff(red_single.mef_score)),
                "nash_gap_sampled": nash_gap(to_payoff(blue_coa.mef_score), to_payoff(red_sampled.mef_score)),
                "blue_doctrinal_alignment": doctrinal_alignment_score(blue_coa),
                "red_doctrinal_alignment_single": doctrinal_alignment_score(red_single),
                "red_doctrinal_alignment_sampled": doctrinal_alignment_score(red_sampled),
                "candidate_diversity": comparison.diversity,
                "candidate_mef_spread": comparison.mef_spread,
                "n_pareto_optimal": len(comparison.pareto_optimal_ids),
                "blue_wins_single": wargame_single["winner"] == "blue",
                "blue_wins_sampled": wargame_sampled["winner"] == "blue",
                # Per-candidate values for scatter figure (first 10 rows only)
                f"candidate_mef_values_{row_idx}": (
                    json.dumps([c.mef_score for c in candidates]) if row_idx < 10 else None
                ),
                f"candidate_da_values_{row_idx}": (
                    json.dumps([doctrinal_alignment_score(c) for c in candidates]) if row_idx < 10 else None
                ),
            }

            if red_llm is not None and wargame_llm is not None:
                row["gbc_llm"] = gbc_score(blue_coa, red_llm)
                row["nash_gap_llm"] = nash_gap(to_payoff(blue_coa.mef_score), to_payoff(red_llm.mef_score))
                row["red_doctrinal_alignment_llm"] = doctrinal_alignment_score(red_llm)
                row["blue_wins_llm"] = wargame_llm["winner"] == "blue"

            rows.append(row)
            print(f"  [{len(rows):3d}/{ N_SEEDS * 3}] {case.profile.scenario_id}", end="\r")

    print()

    def boot(key: str):
        vals = [r[key] for r in rows if r.get(key) is not None]
        return bootstrap_ci(lambda s: mean(s), vals, n_boot=1000, seed=0)

    print(f"\n== Best-response comparison ({len(rows)} scenarios) ==")
    print(f"GBC (single):    {boot('gbc_single')}")
    print(f"GBC (sampled):   {boot('gbc_sampled')}")
    if has_llm:
        print(f"GBC (LLM):       {boot('gbc_llm')}")
    print(f"Nash gap (single):  {boot('nash_gap_single')}")
    print(f"Nash gap (sampled): {boot('nash_gap_sampled')}")
    if has_llm:
        print(f"Nash gap (LLM):    {boot('nash_gap_llm')}")

    print("\n== Doctrinal alignment ==")
    print(f"Blue (fixed):               {boot('blue_doctrinal_alignment')}")
    print(f"Red, single-sample:         {boot('red_doctrinal_alignment_single')}")
    print(f"Red, sampled-best-response: {boot('red_doctrinal_alignment_sampled')}")
    if has_llm:
        print(f"Red, LLM:                   {boot('red_doctrinal_alignment_llm')}")

    print("\n== Multi-COA comparison ==")
    print(f"Candidate diversity:   {boot('candidate_diversity')}")
    print(f"Candidate MEF spread:  {boot('candidate_mef_spread')}")
    print(f"Pareto-optimal count:  {boot('n_pareto_optimal')}")

    bwr_single = mean(r["blue_wins_single"] for r in rows)
    bwr_sampled = mean(r["blue_wins_sampled"] for r in rows)
    print(f"\n== Lanchester wargame: BLUE win rate ==")
    print(f"vs. single-sample RED:        {bwr_single:.3f}")
    print(f"vs. sampled-best-response RED: {bwr_sampled:.3f}")
    if has_llm:
        bwr_llm = mean(r["blue_wins_llm"] for r in rows if "blue_wins_llm" in r)
        print(f"vs. LLM RED:                  {bwr_llm:.3f}")

    print("\n== Scenario framing sensitivity ==")
    framing_deltas = []
    for i in range(N_SEEDS):
        seed = 200 + i
        for factory in (make_urban_operations_case, make_maritime_operations_case, make_multi_domain_operations_case):
            scores = {
                framing: doctrinal_alignment_score(factory(seed=seed, framing=framing).seed_coas[0])
                for framing in ("blue", "neutral", "adversary")
            }
            framing_deltas.append(framing_sensitivity_delta(scores))
    print(f"Framing sensitivity delta: {bootstrap_ci(lambda s: mean(s), framing_deltas, n_boot=1000, seed=0)}")

    # Export results
    output = Path("results/coa-bench/main")
    output.mkdir(parents=True, exist_ok=True)

    csv_rows = [{k: v for k, v in r.items() if not k.startswith("candidate_mef_values_") and not k.startswith("candidate_da_values_")} for r in rows]
    with open(output / "rows.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)

    summary_keys = [
        "gbc_single", "gbc_sampled", "nash_gap_single", "nash_gap_sampled",
        "blue_doctrinal_alignment", "red_doctrinal_alignment_single",
        "red_doctrinal_alignment_sampled", "candidate_diversity",
        "candidate_mef_spread", "n_pareto_optimal",
    ]
    if has_llm:
        summary_keys += ["gbc_llm", "nash_gap_llm", "red_doctrinal_alignment_llm"]

    with open(output / "summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "mean", "ci_lower", "ci_upper", "n_boot", "confidence"])
        for name in summary_keys:
            result = boot(name)
            writer.writerow([name, result.mean, result.lower, result.upper, result.n_boot, result.confidence])
        writer.writerow(["framing_sensitivity_delta",
                         *[getattr(bootstrap_ci(lambda s: mean(s), framing_deltas, n_boot=1000, seed=0), a)
                           for a in ("mean", "lower", "upper", "n_boot", "confidence")]])

    details = {
        "n_scenarios": len(rows),
        "n_seeds": N_SEEDS,
        "n_samples": N_SAMPLES,
        "llm_policy_used": has_llm,
        "llm_model": "claude-haiku-4-5-20251001" if has_llm else None,
        "blue_win_rate_single": bwr_single,
        "blue_win_rate_sampled": bwr_sampled,
        "blue_win_rate_llm": (mean(r["blue_wins_llm"] for r in rows if "blue_wins_llm" in r) if has_llm else None),
        "source": "experiments/coa_bench_experiment.py -- outcomes from the coageneration "
                  "self-play simulator, not a production deployment.",
    }
    with open(output / "details.json", "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2)

    _save_figures(rows)
    print(f"\nResults written to {output}/")


if __name__ == "__main__":
    main()
