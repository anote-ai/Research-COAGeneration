"""Run learned-router ablations on the held-out executable task split."""

from __future__ import annotations

from pathlib import Path

from metarouter.executable_benchmark import export_executable_results, run_executable_benchmark
from metarouter.executable_tasks import generate_executable_tasks
from metarouter.text_router import (
    CalibratedTextOperationModel,
    LearnedBudgetPolicy,
    LearnedOneShotPolicy,
    tune_threshold,
)


def main() -> None:
    train_tasks = generate_executable_tasks("train", 72)
    dev_tasks = generate_executable_tasks("dev", 24)
    test_tasks = generate_executable_tasks("test", 36)

    full_model = CalibratedTextOperationModel().fit(train_tasks, dev_tasks)
    full_threshold = tune_threshold(full_model, dev_tasks)

    word_model = CalibratedTextOperationModel(use_character_features=False).fit(
        train_tasks, dev_tasks
    )
    word_threshold = tune_threshold(word_model, dev_tasks)

    uncalibrated_model = CalibratedTextOperationModel().fit(train_tasks, dev_tasks)
    uncalibrated_model.temperatures = {
        action: 1.0 for action in uncalibrated_model.temperatures
    }
    uncalibrated_threshold = tune_threshold(uncalibrated_model, dev_tasks)

    policies = [
        LearnedBudgetPolicy(full_model, full_threshold, name="full"),
        LearnedOneShotPolicy(full_model),
        LearnedBudgetPolicy(
            word_model, word_threshold, name="word_only"
        ),
        LearnedBudgetPolicy(
            uncalibrated_model,
            uncalibrated_threshold,
            name="no_calibration",
        ),
        LearnedBudgetPolicy(
            full_model,
            full_threshold,
            max_actions=5,
            name="no_budget",
            enforce_budget=False,
        ),
    ]
    traces = run_executable_benchmark(test_tasks, policies)
    output = Path("results/meta-routing/aaai2027/ablations")
    export_executable_results(
        traces,
        output,
        full_model,
        dev_tasks,
        full_threshold,
        treatment="full",
    )
    print(f"Exported {len(traces):,} ablation traces to {output}")


if __name__ == "__main__":
    main()
