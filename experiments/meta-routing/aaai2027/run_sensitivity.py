"""Evaluate sample efficiency and threshold sensitivity without model retuning."""

from __future__ import annotations

import csv
from pathlib import Path

from metarouter.executable_benchmark import run_executable_benchmark
from metarouter.executable_evaluation import summarize_executable_policy
from metarouter.executable_tasks import generate_executable_tasks
from metarouter.text_router import (
    CalibratedTextOperationModel,
    LearnedBudgetPolicy,
    tune_threshold,
)


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _evaluate(
    policy: LearnedBudgetPolicy,
    tasks,
) -> dict[str, float]:
    summary = summarize_executable_policy(
        run_executable_benchmark(tasks, [policy])
    )
    return {
        "success": summary.success_rate,
        "cost": summary.mean_cost,
        "route_exact_match": summary.route_exact_match,
        "action_f1": summary.action_f1,
    }


def main() -> None:
    output = Path("results/meta-routing/aaai2027/sensitivity")
    dev = generate_executable_tasks("dev", 24)
    test = generate_executable_tasks("test", 36)
    challenge = generate_executable_tasks("challenge", 36)

    learning_rows: list[dict[str, object]] = []
    for per_workload in (12, 24, 36, 48, 72):
        train = generate_executable_tasks("train", per_workload)
        model = CalibratedTextOperationModel().fit(train, dev)
        threshold = tune_threshold(model, dev)
        policy = LearnedBudgetPolicy(model, threshold=threshold)
        standard_metrics = _evaluate(policy, test)
        challenge_metrics = _evaluate(policy, challenge)
        learning_rows.append(
            {
                "training_tasks": len(train),
                "threshold": threshold,
                **{f"test_{key}": value for key, value in standard_metrics.items()},
                **{
                    f"challenge_{key}": value
                    for key, value in challenge_metrics.items()
                },
            }
        )
    _write(output / "learning_curve.csv", learning_rows)

    full_train = generate_executable_tasks("train", 72)
    full_model = CalibratedTextOperationModel().fit(full_train, dev)
    threshold_rows: list[dict[str, object]] = []
    for threshold in (0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70):
        policy = LearnedBudgetPolicy(full_model, threshold=threshold)
        standard_metrics = _evaluate(policy, test)
        challenge_metrics = _evaluate(policy, challenge)
        threshold_rows.append(
            {
                "threshold": threshold,
                **{f"test_{key}": value for key, value in standard_metrics.items()},
                **{
                    f"challenge_{key}": value
                    for key, value in challenge_metrics.items()
                },
            }
        )
    _write(output / "thresholds.csv", threshold_rows)
    print(f"Wrote sensitivity results to {output}")


if __name__ == "__main__":
    main()
