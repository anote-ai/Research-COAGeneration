"""Execute routed operations and grade answers without sampled outcomes."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from statistics import mean
from typing import Any

from .executable_models import ExecutableTask, ExecutableTrace
from .models import RouteAction, RoutePlan


ACTION_COST = {
    RouteAction.DECOMPOSE: 0.45,
    RouteAction.USE_TOOL: 1.00,
    RouteAction.EXECUTE_CODE: 1.15,
    RouteAction.DELEGATE: 1.40,
    RouteAction.VERIFY: 0.65,
    RouteAction.ANSWER: 0.30,
}


@dataclass
class _State:
    decomposed: bool = False
    candidate: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)
    failed_action: RouteAction | None = None


def _normalize(answer: str) -> str:
    return re.sub(r"\s+", " ", answer.strip().lower())


def _direct_answer(task: ExecutableTask) -> str | None:
    if task.kind == "direct_literal":
        return str(task.payload["answer"])
    return None


def _decompose(task: ExecutableTask, state: _State) -> None:
    state.decomposed = True
    if task.kind == "research_multihop":
        state.artifacts["subqueries"] = [task.payload["person"], task.payload["lab"]]
    elif task.kind == "filtered_sum":
        state.artifacts["filter"] = task.payload["group"]
    elif task.kind == "crossfield_check":
        state.artifacts["fields"] = ["region", "serial"]


def _use_tool(task: ExecutableTask, state: _State) -> None:
    if RouteAction.USE_TOOL in task.unavailable_actions:
        state.failed_action = RouteAction.USE_TOOL
        return
    if task.kind == "research_fact":
        matches = [
            doc
            for doc in task.payload["documents"]
            if doc["subject"] == task.payload["subject"]
            and doc["field"] == task.payload["field"]
        ]
        state.artifacts["documents"] = matches
        state.candidate = str(matches[0]["value"]) if matches else None
    elif task.kind == "research_multihop":
        docs = task.payload["documents"]
        first = next(doc for doc in docs if doc["subject"] == task.payload["person"])
        state.artifacts["documents"] = [first]
        state.candidate = str(first["value"])
        if state.decomposed:
            second = next(doc for doc in docs if doc["subject"] == first["value"])
            state.artifacts["documents"].append(second)
            state.candidate = str(second["value"])
    elif task.kind == "research_conflict":
        documents = list(task.payload["documents"])
        state.artifacts["documents"] = documents
        state.candidate = str(documents[0]["value"])
    elif task.kind == "document_extract":
        field = re.escape(str(task.payload["field"]))
        match = re.search(rf"{field}:\s*([^;]+)", task.payload["document"])
        state.candidate = match.group(1).strip() if match else None
    elif task.kind == "invoice_reconcile":
        state.artifacts["items"] = list(task.payload["items"])
        state.artifacts["stated_total"] = task.payload["stated_total"]
        state.candidate = str(task.payload["stated_total"])
    elif task.kind == "date_normalize":
        state.artifacts["raw_date"] = task.payload["raw_date"]
        state.artifacts["locale"] = task.payload["locale"]
        state.candidate = str(task.payload["raw_date"])
    elif task.kind == "crossfield_check":
        state.artifacts["region"] = task.payload["region"]
        if state.decomposed:
            state.artifacts["serial"] = task.payload["serial"]
        state.candidate = str(task.payload["region"])


def _execute_code(task: ExecutableTask, state: _State) -> None:
    if task.kind == "aggregate":
        values = task.payload["values"]
        operation = task.payload["operation"]
        if operation == "sum":
            state.candidate = str(sum(values))
        elif operation == "maximum":
            state.candidate = str(max(values))
        else:
            state.candidate = f"{mean(values):.2f}"
    elif task.kind == "filtered_sum":
        rows = task.payload["rows"]
        if state.decomposed:
            group = state.artifacts["filter"]
            state.candidate = str(sum(value for label, value in rows if label == group))
        else:
            state.candidate = str(sum(value for _label, value in rows))
    elif task.kind == "invoice_reconcile" and "items" in state.artifacts:
        state.artifacts["computed_total"] = sum(state.artifacts["items"])


def _delegate(task: ExecutableTask, state: _State) -> None:
    if task.kind == "research_outage":
        state.candidate = str(task.payload["specialist_answer"])
    elif task.kind == "date_normalize" and "raw_date" in state.artifacts:
        first, second, year = map(int, state.artifacts["raw_date"].split("/"))
        if state.artifacts["locale"] == "EU":
            day, month = first, second
        else:
            month, day = first, second
        state.candidate = f"{year}-{month:02d}-{day:02d}"


def _verify(task: ExecutableTask, state: _State) -> None:
    if task.kind == "research_conflict" and state.artifacts.get("documents"):
        newest = max(state.artifacts["documents"], key=lambda doc: doc["year"])
        state.candidate = str(newest["value"])
    elif task.kind == "invoice_reconcile" and "computed_total" in state.artifacts:
        state.candidate = str(state.artifacts["computed_total"])
    elif task.kind == "crossfield_check" and {
        "region",
        "serial",
    }.issubset(state.artifacts):
        state.candidate = f"{state.artifacts['region']}-{state.artifacts['serial']}"


def _execute_once(task: ExecutableTask, plan: RoutePlan) -> tuple[str, str | None]:
    state = _State()
    handlers = {
        RouteAction.DECOMPOSE: _decompose,
        RouteAction.USE_TOOL: _use_tool,
        RouteAction.EXECUTE_CODE: _execute_code,
        RouteAction.DELEGATE: _delegate,
        RouteAction.VERIFY: _verify,
    }
    for action in plan.actions:
        if state.failed_action is not None:
            break
        if action == RouteAction.ANSWER:
            if state.candidate is None:
                state.candidate = _direct_answer(task)
            break
        handlers[action](task, state)
    answer = state.candidate or ""
    failure = None
    if state.failed_action is not None:
        failure = f"{state.failed_action.value}_unavailable"
    elif not answer:
        failure = "no_answer"
    elif _normalize(answer) != _normalize(task.expected_answer):
        failure = "incorrect_answer"
    return answer, failure


def execute_task(
    task: ExecutableTask,
    plan: RoutePlan,
    policy_name: str,
    route_latency_ms: float,
    timing_repetitions: int = 5,
) -> ExecutableTrace:
    """Run a plan and use repeated execution only to stabilize latency timing."""
    if timing_repetitions < 1:
        raise ValueError("timing_repetitions must be positive")
    start = time.perf_counter_ns()
    answer = ""
    failure: str | None = None
    for _ in range(timing_repetitions):
        answer, failure = _execute_once(task, plan)
    execution_latency_ms = (
        (time.perf_counter_ns() - start) / 1_000_000 / timing_repetitions
    )
    support_actions = tuple(
        action for action in plan.actions if action != RouteAction.ANSWER
    )
    cost = sum(ACTION_COST[action] for action in plan.actions)
    return ExecutableTrace(
        policy=policy_name,
        task_id=task.task_id,
        split=task.split,
        workload=task.workload.value,
        kind=task.kind,
        actions=tuple(action.value for action in plan.actions),
        required_actions=tuple(action.value for action in task.required_actions),
        success=failure is None,
        answer=answer,
        expected_answer=task.expected_answer,
        cost=round(cost, 4),
        route_latency_ms=route_latency_ms,
        execution_latency_ms=execution_latency_ms,
        within_cost_budget=cost <= task.cost_budget,
        route_exact_match=support_actions == task.required_actions,
        confidence=plan.confidence,
        rationale=plan.rationale,
        failure_mode=failure,
    )
