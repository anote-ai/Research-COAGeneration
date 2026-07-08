"""Tests for raw-text routing and machine-checked executable tasks."""

from __future__ import annotations

import csv

from metarouter.executable_benchmark import (
    export_executable_results,
    export_executable_tasks,
    run_executable_benchmark,
)
from metarouter.executable_executor import execute_task
from metarouter.executable_tasks import generate_executable_tasks
from metarouter.models import RouteAction, RoutePlan, Workload
from metarouter.text_router import DirectPolicy, OraclePolicy, executable_policies


def test_executable_splits_are_balanced_and_hold_out_templates() -> None:
    train = generate_executable_tasks("train", 10)
    test = generate_executable_tasks("test", 10)
    assert len(train) == len(test) == 30
    assert {
        workload: sum(task.workload == workload for task in test)
        for workload in Workload
    } == {workload: 10 for workload in Workload}
    train_prompt = next(task.prompt for task in train if task.kind == "aggregate")
    test_prompt = next(task.prompt for task in test if task.kind == "aggregate")
    assert train_prompt != test_prompt
    challenge = generate_executable_tasks("challenge", 10)
    challenge_prompt = next(
        task.prompt for task in challenge if task.kind == "aggregate"
    )
    assert challenge_prompt not in {train_prompt, test_prompt}


def test_oracle_routes_produce_machine_checked_answers() -> None:
    tasks = generate_executable_tasks("test", 10)
    traces = run_executable_benchmark(tasks, [OraclePolicy()])
    assert all(trace.success for trace in traces)
    assert all(trace.route_exact_match for trace in traces)


def test_unavailable_tool_fails_but_delegation_succeeds() -> None:
    task = next(
        task
        for task in generate_executable_tasks("test", 10)
        if task.kind == "research_outage"
    )
    failed = execute_task(
        task,
        RoutePlan(actions=(RouteAction.USE_TOOL, RouteAction.ANSWER)),
        "tool",
        0.0,
    )
    recovered = execute_task(
        task,
        RoutePlan(actions=(RouteAction.DELEGATE, RouteAction.ANSWER)),
        "delegate",
        0.0,
    )
    assert not failed.success
    assert failed.failure_mode == "use_tool_unavailable"
    assert recovered.success


def test_learned_router_uses_only_raw_prompt_at_inference() -> None:
    train = generate_executable_tasks("train", 15)
    dev = generate_executable_tasks("dev", 10)
    test = generate_executable_tasks("test", 10)
    policies, _model, _threshold = executable_policies(train, dev)
    learned = next(policy for policy in policies if policy.name == "learned_budget")
    task = next(task for task in test if task.kind == "invoice_reconcile")
    plan = learned.route(task)
    assert RouteAction.USE_TOOL in plan.actions
    assert plan.actions[-1] == RouteAction.ANSWER


def test_executable_exports(tmp_path) -> None:
    train = generate_executable_tasks("train", 10)
    dev = generate_executable_tasks("dev", 10)
    test = generate_executable_tasks("test", 10)
    policies, model, threshold = executable_policies(train, dev)
    traces = run_executable_benchmark(test, [DirectPolicy(), OraclePolicy()])
    export_executable_tasks(test, tmp_path / "test")
    export_executable_results(
        traces,
        tmp_path,
        model,
        dev,
        threshold,
        treatment="oracle",
    )
    with (tmp_path / "summary.csv").open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["policy"] for row in rows} == {"direct", "oracle"}
    assert (tmp_path / "comparisons.csv").exists()
    assert (tmp_path / "details.json").exists()
