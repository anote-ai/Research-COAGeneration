"""Deterministic generation of balanced, production-like benchmark tasks."""

from __future__ import annotations

import random

from .models import TaskSpec, Workload


_PROFILES: dict[Workload, dict[str, float]] = {
    Workload.DATA_ANALYSIS: {
        "decomposition_need": 0.48,
        "tool_need": 0.34,
        "code_need": 0.78,
        "delegation_need": 0.30,
        "verification_need": 0.62,
    },
    Workload.RESEARCH: {
        "decomposition_need": 0.70,
        "tool_need": 0.76,
        "code_need": 0.18,
        "delegation_need": 0.58,
        "verification_need": 0.66,
    },
    Workload.DOCUMENT_PROCESSING: {
        "decomposition_need": 0.42,
        "tool_need": 0.64,
        "code_need": 0.46,
        "delegation_need": 0.24,
        "verification_need": 0.74,
    },
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def generate_tasks(
    tasks_per_workload: int = 60,
    seed: int = 2026,
) -> list[TaskSpec]:
    """Generate a balanced suite with observable within-workload variation."""
    if tasks_per_workload < 4:
        raise ValueError("tasks_per_workload must be at least 4")

    rng = random.Random(seed)
    tasks: list[TaskSpec] = []
    for workload in Workload:
        profile = _PROFILES[workload]
        for index in range(tasks_per_workload):
            difficulty = 1 + (index % 4)
            difficulty_shift = (difficulty - 2.5) * 0.055
            jitter = {key: rng.uniform(-0.25, 0.25) for key in profile}
            needs = {
                key: _clamp(value + difficulty_shift + jitter[key])
                for key, value in profile.items()
            }
            ambiguity = _clamp(
                0.18 + 0.14 * (difficulty - 1) + rng.uniform(-0.12, 0.12)
            )
            tasks.append(
                TaskSpec(
                    task_id=f"{workload.value}-{index:03d}",
                    workload=workload,
                    difficulty=difficulty,
                    ambiguity=ambiguity,
                    **needs,
                )
            )
    return tasks

