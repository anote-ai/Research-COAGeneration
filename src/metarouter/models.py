"""Typed records for the meta-routing benchmark."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Workload(str, Enum):
    DATA_ANALYSIS = "data_analysis"
    RESEARCH = "research"
    DOCUMENT_PROCESSING = "document_processing"


class RouteAction(str, Enum):
    DECOMPOSE = "decompose"
    USE_TOOL = "use_tool"
    EXECUTE_CODE = "execute_code"
    DELEGATE = "delegate"
    VERIFY = "verify"
    ANSWER = "answer"


@dataclass(frozen=True)
class TaskSpec:
    """Observable task features used by routing policies."""

    task_id: str
    workload: Workload
    difficulty: int
    ambiguity: float
    decomposition_need: float
    tool_need: float
    code_need: float
    delegation_need: float
    verification_need: float
    cost_budget: float = 8.0
    latency_budget_s: float = 90.0

    def __post_init__(self) -> None:
        if not 1 <= self.difficulty <= 5:
            raise ValueError("difficulty must be between 1 and 5")
        for name in (
            "ambiguity",
            "decomposition_need",
            "tool_need",
            "code_need",
            "delegation_need",
            "verification_need",
        ):
            value = getattr(self, name)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")


@dataclass(frozen=True)
class RoutePlan:
    actions: tuple[RouteAction, ...]
    adaptive_recovery: bool = False
    confidence: float = 0.5
    rationale: str = ""

    def __post_init__(self) -> None:
        if not self.actions or self.actions[-1] != RouteAction.ANSWER:
            raise ValueError("every route must end with answer")
        if len(set(self.actions)) != len(self.actions):
            raise ValueError("route actions must be unique")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")


@dataclass(frozen=True)
class ExecutionTrace:
    policy: str
    task_id: str
    workload: str
    seed: int
    actions: tuple[str, ...]
    success: bool
    expected_success: float
    cost: float
    latency_s: float
    retries: int
    route_valid: bool
    within_cost_budget: bool
    within_latency_budget: bool
    confidence: float
    rationale: str
    failure_mode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["actions"] = "|".join(self.actions)
        return data
