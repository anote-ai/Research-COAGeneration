"""Typed records for the executable meta-routing benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .models import RouteAction, RoutePlan, Workload


@dataclass(frozen=True)
class ExecutableTask:
    """A raw-text task with a machine-checkable answer and executable payload."""

    task_id: str
    split: str
    workload: Workload
    prompt: str
    kind: str
    payload: dict[str, Any]
    expected_answer: str
    required_actions: tuple[RouteAction, ...]
    unavailable_actions: tuple[RouteAction, ...] = ()
    cost_budget: float = 4.5

    def __post_init__(self) -> None:
        if self.split not in {"train", "dev", "test", "challenge"}:
            raise ValueError("split must be train, dev, test, or challenge")
        if RouteAction.ANSWER in self.required_actions:
            raise ValueError("required_actions contains support operations only")
        if len(set(self.required_actions)) != len(self.required_actions):
            raise ValueError("required actions must be unique")
        if self.cost_budget <= 0:
            raise ValueError("cost_budget must be positive")


@dataclass(frozen=True)
class ExecutableTrace:
    policy: str
    task_id: str
    split: str
    workload: str
    kind: str
    actions: tuple[str, ...]
    required_actions: tuple[str, ...]
    success: bool
    answer: str
    expected_answer: str
    cost: float
    route_latency_ms: float
    execution_latency_ms: float
    within_cost_budget: bool
    route_exact_match: bool
    confidence: float
    rationale: str
    failure_mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["actions"] = "|".join(self.actions)
        data["required_actions"] = "|".join(self.required_actions)
        return data


class ExecutablePolicy:
    """Minimal interface shared by executable benchmark policies."""

    name: str

    def route(self, task: ExecutableTask) -> RoutePlan:
        raise NotImplementedError
