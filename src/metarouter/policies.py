"""Routing policies compared by the benchmark."""

from __future__ import annotations

import random
from abc import ABC, abstractmethod

from .models import RouteAction, RoutePlan, TaskSpec, Workload


class RoutingPolicy(ABC):
    name: str

    @abstractmethod
    def route(self, task: TaskSpec, rng: random.Random) -> RoutePlan:
        raise NotImplementedError


class FixedPolicy(RoutingPolicy):
    def __init__(self, name: str, actions: tuple[RouteAction, ...]) -> None:
        self.name = name
        self._actions = actions

    def route(self, task: TaskSpec, rng: random.Random) -> RoutePlan:
        del task, rng
        return RoutePlan(
            actions=(*self._actions, RouteAction.ANSWER),
            confidence=0.5,
            rationale="fixed route",
        )


class RandomPolicy(RoutingPolicy):
    name = "random"
    _support_actions = (
        RouteAction.DECOMPOSE,
        RouteAction.USE_TOOL,
        RouteAction.EXECUTE_CODE,
        RouteAction.DELEGATE,
        RouteAction.VERIFY,
    )

    def route(self, task: TaskSpec, rng: random.Random) -> RoutePlan:
        del task
        count = rng.choice((1, 2))
        actions = tuple(rng.sample(self._support_actions, count))
        return RoutePlan(actions=(*actions, RouteAction.ANSWER), rationale="random route")


class StaticWorkloadPolicy(RoutingPolicy):
    """A competent fixed rule table that cannot inspect task-level needs."""

    name = "static_workload"

    def route(self, task: TaskSpec, rng: random.Random) -> RoutePlan:
        del rng
        if task.workload == Workload.DATA_ANALYSIS:
            actions = (RouteAction.EXECUTE_CODE, RouteAction.VERIFY)
        elif task.workload == Workload.RESEARCH:
            actions = (RouteAction.DECOMPOSE, RouteAction.USE_TOOL)
        else:
            actions = (RouteAction.USE_TOOL, RouteAction.VERIFY)
        return RoutePlan(
            actions=(*actions, RouteAction.ANSWER),
            confidence=0.7,
            rationale="workload-level rule table",
        )


class OneShotRouter(RoutingPolicy):
    """Select the single most useful operation without observing execution."""

    name = "one_shot"

    def route(self, task: TaskSpec, rng: random.Random) -> RoutePlan:
        del rng
        candidates = {
            RouteAction.DECOMPOSE: task.decomposition_need,
            RouteAction.USE_TOOL: task.tool_need,
            RouteAction.EXECUTE_CODE: task.code_need,
            RouteAction.DELEGATE: task.delegation_need,
            RouteAction.VERIFY: task.verification_need,
        }
        action, score = max(candidates.items(), key=lambda item: item[1])
        return RoutePlan(
            actions=(action, RouteAction.ANSWER),
            confidence=score,
            rationale=f"highest task-level need: {action.value}",
        )


class AdaptiveRouter(RoutingPolicy):
    """Budget-aware policy that composes operations and enables recovery."""

    def __init__(
        self,
        name: str = "adaptive",
        max_actions: int = 3,
        recovery: bool = True,
        disabled_actions: frozenset[RouteAction] = frozenset(),
    ) -> None:
        if max_actions < 1:
            raise ValueError("max_actions must be positive")
        self.name = name
        self.max_actions = max_actions
        self.recovery = recovery
        self.disabled_actions = disabled_actions

    def route(self, task: TaskSpec, rng: random.Random) -> RoutePlan:
        del rng
        scored = [
            (RouteAction.DECOMPOSE, task.decomposition_need),
            (RouteAction.USE_TOOL, task.tool_need),
            (RouteAction.EXECUTE_CODE, task.code_need),
            (RouteAction.DELEGATE, task.delegation_need),
            (RouteAction.VERIFY, task.verification_need),
        ]
        scored = [item for item in scored if item[0] not in self.disabled_actions]
        threshold = 0.66 if task.difficulty <= 2 else 0.56
        selected = [item for item in scored if item[1] >= threshold]
        selected.sort(key=lambda item: item[1], reverse=True)

        # Limit orchestration overhead while retaining the strongest signals.
        actions = [action for action, _score in selected[: self.max_actions]]
        if not actions:
            actions = [max(scored, key=lambda item: item[1])[0]]
        if RouteAction.DECOMPOSE in actions:
            actions.remove(RouteAction.DECOMPOSE)
            actions.insert(0, RouteAction.DECOMPOSE)
        if RouteAction.VERIFY in actions:
            actions.remove(RouteAction.VERIFY)
            actions.append(RouteAction.VERIFY)

        confidence = sum(
            score for action, score in selected[: self.max_actions]
        ) / max(1, len(actions))
        return RoutePlan(
            actions=(*actions, RouteAction.ANSWER),
            adaptive_recovery=self.recovery,
            confidence=min(1.0, confidence),
            rationale="task-level needs with budgeted composition and recovery",
        )


def default_policies() -> list[RoutingPolicy]:
    return [
        FixedPolicy("direct", ()),
        FixedPolicy("always_decompose", (RouteAction.DECOMPOSE,)),
        FixedPolicy("always_tool", (RouteAction.USE_TOOL,)),
        FixedPolicy("always_code", (RouteAction.EXECUTE_CODE,)),
        RandomPolicy(),
        StaticWorkloadPolicy(),
        OneShotRouter(),
        AdaptiveRouter(),
    ]


def ablation_policies() -> list[RoutingPolicy]:
    return [
        AdaptiveRouter(),
        AdaptiveRouter(name="adaptive_no_recovery", recovery=False),
        AdaptiveRouter(name="adaptive_single_action", max_actions=1),
        AdaptiveRouter(
            name="adaptive_no_decompose",
            disabled_actions=frozenset({RouteAction.DECOMPOSE}),
        ),
        AdaptiveRouter(
            name="adaptive_no_verify",
            disabled_actions=frozenset({RouteAction.VERIFY}),
        ),
    ]
