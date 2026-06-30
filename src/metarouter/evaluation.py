"""Aggregate metrics and confidence intervals for routing traces."""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import asdict, dataclass
from statistics import mean, stdev

from .models import ExecutionTrace


@dataclass(frozen=True)
class PolicySummary:
    policy: str
    n: int
    success_rate: float
    success_ci95: float
    expected_success: float
    mean_cost: float
    cost_per_success: float
    mean_latency_s: float
    retry_rate: float
    budget_compliance: float
    utility: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PairedComparison:
    treatment: str
    baseline: str
    success_difference: float
    success_difference_ci95: float
    cost_difference: float
    latency_difference_s: float

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _seed_rates(traces: list[ExecutionTrace]) -> list[float]:
    grouped: dict[int, list[ExecutionTrace]] = defaultdict(list)
    for trace in traces:
        grouped[trace.seed].append(trace)
    return [mean(float(item.success) for item in items) for items in grouped.values()]


def summarize_policy(traces: list[ExecutionTrace]) -> PolicySummary:
    if not traces:
        raise ValueError("at least one trace is required")
    policy_names = {trace.policy for trace in traces}
    if len(policy_names) != 1:
        raise ValueError("traces must belong to one policy")

    success_rate = mean(float(trace.success) for trace in traces)
    seed_rates = _seed_rates(traces)
    ci95 = 0.0
    if len(seed_rates) > 1:
        ci95 = 1.96 * stdev(seed_rates) / math.sqrt(len(seed_rates))
    mean_cost = mean(trace.cost for trace in traces)
    mean_latency = mean(trace.latency_s for trace in traces)
    cost_per_success = mean_cost / success_rate if success_rate else math.inf
    budget_compliance = mean(
        float(trace.within_cost_budget and trace.within_latency_budget)
        for trace in traces
    )
    # Utility is secondary; raw success, cost, and latency remain primary.
    utility = success_rate - 0.025 * mean_cost - 0.0015 * mean_latency
    return PolicySummary(
        policy=next(iter(policy_names)),
        n=len(traces),
        success_rate=success_rate,
        success_ci95=ci95,
        expected_success=mean(trace.expected_success for trace in traces),
        mean_cost=mean_cost,
        cost_per_success=cost_per_success,
        mean_latency_s=mean_latency,
        retry_rate=mean(float(trace.retries > 0) for trace in traces),
        budget_compliance=budget_compliance,
        utility=utility,
    )


def summarize_all(traces: list[ExecutionTrace]) -> list[PolicySummary]:
    grouped: dict[str, list[ExecutionTrace]] = defaultdict(list)
    for trace in traces:
        grouped[trace.policy].append(trace)
    summaries = [summarize_policy(items) for items in grouped.values()]
    return sorted(summaries, key=lambda item: item.utility, reverse=True)


def workload_success(traces: list[ExecutionTrace]) -> dict[str, dict[str, float]]:
    grouped: dict[tuple[str, str], list[ExecutionTrace]] = defaultdict(list)
    for trace in traces:
        grouped[(trace.policy, trace.workload)].append(trace)
    result: dict[str, dict[str, float]] = defaultdict(dict)
    for (policy, workload), items in grouped.items():
        result[policy][workload] = mean(float(item.success) for item in items)
    return dict(result)


def paired_comparison(
    traces: list[ExecutionTrace],
    treatment: str,
    baseline: str,
) -> PairedComparison:
    """Compare policies using paired seed-level aggregates."""
    grouped: dict[tuple[str, int], list[ExecutionTrace]] = defaultdict(list)
    for trace in traces:
        if trace.policy in {treatment, baseline}:
            grouped[(trace.policy, trace.seed)].append(trace)
    seeds = sorted(
        {seed for policy, seed in grouped if policy == treatment}
        & {seed for policy, seed in grouped if policy == baseline}
    )
    if not seeds:
        raise ValueError("no paired seeds found for requested policies")

    success_differences: list[float] = []
    cost_differences: list[float] = []
    latency_differences: list[float] = []
    for seed in seeds:
        treatment_items = grouped[(treatment, seed)]
        baseline_items = grouped[(baseline, seed)]
        success_differences.append(
            mean(float(item.success) for item in treatment_items)
            - mean(float(item.success) for item in baseline_items)
        )
        cost_differences.append(
            mean(item.cost for item in treatment_items)
            - mean(item.cost for item in baseline_items)
        )
        latency_differences.append(
            mean(item.latency_s for item in treatment_items)
            - mean(item.latency_s for item in baseline_items)
        )
    ci95 = 0.0
    if len(success_differences) > 1:
        ci95 = 1.96 * stdev(success_differences) / math.sqrt(len(success_differences))
    return PairedComparison(
        treatment=treatment,
        baseline=baseline,
        success_difference=mean(success_differences),
        success_difference_ci95=ci95,
        cost_difference=mean(cost_differences),
        latency_difference_s=mean(latency_differences),
    )
