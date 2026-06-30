"""Seeded offline execution model for routing-policy comparisons."""

from __future__ import annotations

import random

from .models import ExecutionTrace, RouteAction, RoutePlan, TaskSpec


_ACTION_COST = {
    RouteAction.DECOMPOSE: 0.55,
    RouteAction.USE_TOOL: 1.10,
    RouteAction.EXECUTE_CODE: 1.35,
    RouteAction.DELEGATE: 1.65,
    RouteAction.VERIFY: 0.70,
    RouteAction.ANSWER: 0.65,
}

_ACTION_LATENCY = {
    RouteAction.DECOMPOSE: 3.5,
    RouteAction.USE_TOOL: 8.0,
    RouteAction.EXECUTE_CODE: 10.0,
    RouteAction.DELEGATE: 13.0,
    RouteAction.VERIFY: 5.0,
    RouteAction.ANSWER: 4.0,
}

_ACTION_FAILURE = {
    RouteAction.USE_TOOL: 0.08,
    RouteAction.EXECUTE_CODE: 0.07,
    RouteAction.DELEGATE: 0.10,
}

_NEED_FIELD = {
    RouteAction.DECOMPOSE: "decomposition_need",
    RouteAction.USE_TOOL: "tool_need",
    RouteAction.EXECUTE_CODE: "code_need",
    RouteAction.DELEGATE: "delegation_need",
    RouteAction.VERIFY: "verification_need",
}

_BENEFIT = {
    RouteAction.DECOMPOSE: 0.19,
    RouteAction.USE_TOOL: 0.24,
    RouteAction.EXECUTE_CODE: 0.27,
    RouteAction.DELEGATE: 0.18,
    RouteAction.VERIFY: 0.15,
}


class OfflineSimulator:
    """Replay a route against explicit task features and failure assumptions."""

    def execute(
        self,
        task: TaskSpec,
        plan: RoutePlan,
        policy_name: str,
        seed: int,
    ) -> ExecutionTrace:
        rng = random.Random(f"{seed}:{task.task_id}:{policy_name}")
        actions = plan.actions
        route_valid = len(actions) == len(set(actions)) and actions[-1] == RouteAction.ANSWER

        difficulty_factor = 1.0 + 0.08 * (task.difficulty - 1)
        cost = sum(_ACTION_COST[action] for action in actions) * difficulty_factor
        latency = sum(_ACTION_LATENCY[action] for action in actions) * difficulty_factor

        execution_failed = False
        failed_action: RouteAction | None = None
        for action in actions:
            failure_rate = _ACTION_FAILURE.get(action, 0.0)
            if failure_rate and rng.random() < failure_rate:
                execution_failed = True
                failed_action = action
                break

        retries = 0
        if execution_failed and plan.adaptive_recovery:
            retries = 1
            cost += 0.55 * difficulty_factor
            latency += 5.0 * difficulty_factor
            execution_failed = rng.random() >= 0.72

        probability = 0.69 - 0.075 * (task.difficulty - 1) - 0.13 * task.ambiguity
        support_actions = [action for action in actions if action != RouteAction.ANSWER]
        for action in support_actions:
            need = getattr(task, _NEED_FIELD[action])
            probability += _BENEFIT[action] * need
            probability -= 0.045 * (1.0 - need)

        # Long routes impose coordination overhead not captured by monetary cost.
        probability -= max(0, len(support_actions) - 2) * 0.035
        if execution_failed:
            probability -= 0.30
        elif retries:
            probability -= 0.04
        if cost > task.cost_budget:
            probability -= 0.08
        if latency > task.latency_budget_s:
            probability -= 0.08
        probability = max(0.02, min(0.98, probability))

        success = route_valid and rng.random() < probability
        failure_mode: str | None = None
        if not route_valid:
            failure_mode = "invalid_route"
        elif execution_failed:
            failure_mode = f"{failed_action.value}_failure" if failed_action else "execution_failure"
        elif not success:
            failure_mode = "task_failure"

        return ExecutionTrace(
            policy=policy_name,
            task_id=task.task_id,
            workload=task.workload.value,
            seed=seed,
            actions=tuple(action.value for action in actions),
            success=success,
            expected_success=probability,
            cost=round(cost, 4),
            latency_s=round(latency, 4),
            retries=retries,
            route_valid=route_valid,
            within_cost_budget=cost <= task.cost_budget,
            within_latency_budget=latency <= task.latency_budget_s,
            confidence=plan.confidence,
            rationale=plan.rationale,
            failure_mode=failure_mode,
        )
