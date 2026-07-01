"""Orchestration and artifact export for the executable benchmark."""

from __future__ import annotations

import csv
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

from .executable_evaluation import (
    compare_executable,
    summarize_executable_all,
    workload_success,
)
from .executable_executor import execute_task
from .executable_models import ExecutablePolicy, ExecutableTask, ExecutableTrace
from .text_router import CalibratedTextOperationModel


def run_executable_benchmark(
    tasks: list[ExecutableTask],
    policies: list[ExecutablePolicy],
    route_timing_repetitions: int = 5,
    execution_timing_repetitions: int = 5,
) -> list[ExecutableTrace]:
    if not tasks or not policies:
        raise ValueError("tasks and policies are required")
    if route_timing_repetitions < 1:
        raise ValueError("route_timing_repetitions must be positive")
    traces: list[ExecutableTrace] = []
    for policy in policies:
        for task in tasks:
            start = time.perf_counter_ns()
            plan = policy.route(task)
            for _ in range(route_timing_repetitions - 1):
                policy.route(task)
            route_latency_ms = (
                (time.perf_counter_ns() - start)
                / 1_000_000
                / route_timing_repetitions
            )
            traces.append(
                execute_task(
                    task,
                    plan,
                    policy.name,
                    route_latency_ms,
                    timing_repetitions=execution_timing_repetitions,
                )
            )
    return traces


def export_executable_tasks(tasks: list[ExecutableTask], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "task_id": task.task_id,
            "split": task.split,
            "workload": task.workload.value,
            "kind": task.kind,
            "prompt": task.prompt,
            "expected_answer": task.expected_answer,
            "required_actions": "|".join(action.value for action in task.required_actions),
            "unavailable_actions": "|".join(
                action.value for action in task.unavailable_actions
            ),
            "cost_budget": task.cost_budget,
        }
        for task in tasks
    ]
    with (output_dir / "tasks.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_executable_results(
    traces: list[ExecutableTrace],
    output_dir: Path,
    model: CalibratedTextOperationModel,
    dev_tasks: list[ExecutableTask],
    threshold: float,
    treatment: str = "learned_budget",
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = summarize_executable_all(traces)
    with (output_dir / "traces.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(traces[0].to_dict()))
        writer.writeheader()
        writer.writerows(trace.to_dict() for trace in traces)
    with (output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].to_dict()))
        writer.writeheader()
        writer.writerows(summary.to_dict() for summary in summaries)

    policy_names = sorted({trace.policy for trace in traces})
    comparisons = [
        compare_executable(traces, treatment, baseline).to_dict()
        for baseline in policy_names
        if baseline != treatment
    ]
    with (output_dir / "comparisons.csv").open(
        "w", newline="", encoding="utf-8"
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
        writer.writeheader()
        writer.writerows(comparisons)

    failures: dict[str, dict[str, int]] = defaultdict(dict)
    action_counts: dict[str, dict[str, int]] = defaultdict(dict)
    for policy in policy_names:
        selected = [trace for trace in traces if trace.policy == policy]
        failures[policy] = dict(
            Counter(trace.failure_mode or "none" for trace in selected)
        )
        action_counts[policy] = dict(
            Counter(action for trace in selected for action in trace.actions)
        )
    details = {
        "configuration": {
            "test_tasks": len({trace.task_id for trace in traces}),
            "policies": policy_names,
            "learned_threshold": threshold,
            "outcome": "machine-checked executable answer",
            "latency": "local CPU wall-clock milliseconds",
            "cost": "pre-registered normalized operation units, not API dollars",
        },
        "calibration": model.calibration_report(dev_tasks),
        "workload_success": workload_success(traces),
        "failure_modes": dict(failures),
        "action_counts": dict(action_counts),
    }
    (output_dir / "details.json").write_text(
        json.dumps(details, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
