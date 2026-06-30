"""End-to-end benchmark orchestration and artifact export."""

from __future__ import annotations

import csv
import json
import random
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

from .evaluation import PolicySummary, paired_comparison, summarize_all, workload_success
from .models import ExecutionTrace, TaskSpec
from .policies import RoutingPolicy, default_policies
from .simulator import OfflineSimulator
from .workloads import generate_tasks


def run_benchmark(
    tasks: list[TaskSpec] | None = None,
    policies: list[RoutingPolicy] | None = None,
    seeds: int = 30,
) -> list[ExecutionTrace]:
    if seeds < 1:
        raise ValueError("seeds must be positive")
    tasks = tasks or generate_tasks()
    policies = policies or default_policies()
    simulator = OfflineSimulator()
    traces: list[ExecutionTrace] = []
    for seed in range(seeds):
        for policy in policies:
            policy_rng = random.Random(f"{seed}:{policy.name}")
            for task in tasks:
                plan = policy.route(task, policy_rng)
                traces.append(simulator.execute(task, plan, policy.name, seed))
    return traces


def export_tasks(tasks: list[TaskSpec], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for task in tasks:
        row = asdict(task)
        row["workload"] = task.workload.value
        rows.append(row)
    with (output_dir / "tasks.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def export_results(traces: list[ExecutionTrace], output_dir: Path) -> list[PolicySummary]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summaries = summarize_all(traces)

    with (output_dir / "traces.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(traces[0].to_dict()))
        writer.writeheader()
        writer.writerows(trace.to_dict() for trace in traces)

    with (output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0].to_dict()))
        writer.writeheader()
        writer.writerows(summary.to_dict() for summary in summaries)

    failures: dict[str, dict[str, int]] = defaultdict(dict)
    action_counts: dict[str, dict[str, int]] = defaultdict(dict)
    for policy in sorted({trace.policy for trace in traces}):
        policy_traces = [trace for trace in traces if trace.policy == policy]
        failures[policy] = dict(
            Counter(trace.failure_mode or "none" for trace in policy_traces)
        )
        action_counts[policy] = dict(
            Counter(action for trace in policy_traces for action in trace.actions)
        )

    detail = {
        "configuration": {
            "tasks": len({trace.task_id for trace in traces}),
            "seeds": len({trace.seed for trace in traces}),
            "policies": sorted({trace.policy for trace in traces}),
            "note": "Results are from the seeded offline execution model, not production deployment.",
        },
        "action_counts": dict(action_counts),
        "failure_modes": dict(failures),
        "workload_success": workload_success(traces),
    }
    policy_names = {trace.policy for trace in traces}
    if "adaptive" in policy_names:
        comparisons = [
            paired_comparison(traces, "adaptive", baseline).to_dict()
            for baseline in sorted(policy_names - {"adaptive"})
        ]
        with (output_dir / "comparisons.csv").open(
            "w", newline="", encoding="utf-8"
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(comparisons[0]))
            writer.writeheader()
            writer.writerows(comparisons)
    (output_dir / "details.json").write_text(
        json.dumps(detail, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summaries
