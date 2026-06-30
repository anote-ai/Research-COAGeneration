"""Tests for the meta-routing benchmark."""

from __future__ import annotations

import csv
import random

import pytest

from metarouter.benchmark import export_results, export_tasks, run_benchmark
from metarouter.evaluation import paired_comparison, summarize_all, summarize_policy
from metarouter.models import RouteAction, RoutePlan, TaskSpec, Workload
from metarouter.policies import (
    AdaptiveRouter,
    FixedPolicy,
    ablation_policies,
    default_policies,
)
from metarouter.simulator import OfflineSimulator
from metarouter.workloads import generate_tasks


def test_task_validation() -> None:
    with pytest.raises(ValueError):
        TaskSpec(
            task_id="bad",
            workload=Workload.RESEARCH,
            difficulty=0,
            ambiguity=0.2,
            decomposition_need=0.5,
            tool_need=0.5,
            code_need=0.5,
            delegation_need=0.5,
            verification_need=0.5,
        )


def test_route_must_end_with_answer() -> None:
    with pytest.raises(ValueError):
        RoutePlan(actions=(RouteAction.USE_TOOL,))


def test_workloads_are_balanced_and_reproducible() -> None:
    first = generate_tasks(tasks_per_workload=8, seed=7)
    second = generate_tasks(tasks_per_workload=8, seed=7)
    assert first == second
    assert len(first) == 24
    assert {workload: sum(t.workload == workload for t in first) for workload in Workload} == {
        workload: 8 for workload in Workload
    }


def test_adaptive_router_uses_task_level_needs() -> None:
    task = TaskSpec(
        task_id="data-hard",
        workload=Workload.DATA_ANALYSIS,
        difficulty=4,
        ambiguity=0.5,
        decomposition_need=0.75,
        tool_need=0.2,
        code_need=0.95,
        delegation_need=0.1,
        verification_need=0.8,
    )
    plan = AdaptiveRouter().route(task, random.Random(0))
    assert plan.actions == (
        RouteAction.DECOMPOSE,
        RouteAction.EXECUTE_CODE,
        RouteAction.VERIFY,
        RouteAction.ANSWER,
    )
    assert plan.adaptive_recovery


def test_simulator_is_deterministic_for_same_inputs() -> None:
    task = generate_tasks(tasks_per_workload=4)[0]
    policy = AdaptiveRouter()
    plan = policy.route(task, random.Random(0))
    simulator = OfflineSimulator()
    first = simulator.execute(task, plan, policy.name, seed=4)
    second = simulator.execute(task, plan, policy.name, seed=4)
    assert first == second


def test_summary_rejects_mixed_policies() -> None:
    tasks = generate_tasks(tasks_per_workload=4)
    traces = run_benchmark(
        tasks=tasks,
        policies=[FixedPolicy("a", ()), FixedPolicy("b", ())],
        seeds=1,
    )
    with pytest.raises(ValueError):
        summarize_policy(traces)


def test_end_to_end_benchmark_shape() -> None:
    tasks = generate_tasks(tasks_per_workload=4)
    policies = default_policies()
    traces = run_benchmark(tasks=tasks, policies=policies, seeds=3)
    assert len(traces) == len(tasks) * len(policies) * 3
    assert len(summarize_all(traces)) == len(policies)


def test_ablation_policies_have_unique_names() -> None:
    policies = ablation_policies()
    assert len({policy.name for policy in policies}) == len(policies)


def test_paired_comparison() -> None:
    tasks = generate_tasks(tasks_per_workload=4)
    traces = run_benchmark(
        tasks=tasks,
        policies=[FixedPolicy("direct", ()), AdaptiveRouter()],
        seeds=3,
    )
    comparison = paired_comparison(traces, "adaptive", "direct")
    assert comparison.treatment == "adaptive"
    assert comparison.baseline == "direct"


def test_export_results(tmp_path) -> None:
    tasks = generate_tasks(tasks_per_workload=4)
    traces = run_benchmark(tasks=tasks, policies=default_policies()[:2], seeds=2)
    summaries = export_results(traces, tmp_path)
    assert len(summaries) == 2
    assert (tmp_path / "traces.csv").exists()
    assert (tmp_path / "summary.csv").exists()
    assert (tmp_path / "details.json").exists()
    with (tmp_path / "summary.csv").open(newline="", encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == 2


def test_export_tasks(tmp_path) -> None:
    tasks = generate_tasks(tasks_per_workload=4)
    export_tasks(tasks, tmp_path)
    with (tmp_path / "tasks.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 12
    assert rows[0]["workload"] in {workload.value for workload in Workload}
