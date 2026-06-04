"""Evaluation metrics for coageneration."""

from __future__ import annotations

from typing import Dict, List

from .core import CourseOfAction, GameState


def gbc_score(blue_coa: CourseOfAction, red_coa: CourseOfAction) -> float:
    """Game-based comparison score in [0, 1]."""
    raw = blue_coa.mef_score - red_coa.mef_score  # range [-2, 2]
    return (raw + 2.0) / 4.0  # normalise to [0, 1]


def nash_gap(blue_payoff: float, red_payoff: float) -> float:
    """Distance from zero-sum equilibrium (should be 0 at Nash)."""
    return abs(blue_payoff + red_payoff - 1.0)


def robustness_score(
    coa: CourseOfAction, adversarial_responses: List[CourseOfAction]
) -> float:
    """Minimum MEF score across all adversarial responses."""
    if not adversarial_responses:
        return coa.mef_score
    return min(r.mef_score for r in adversarial_responses)


def coa_diversity(coas: List[CourseOfAction]) -> float:
    """Mean pairwise Jaccard distance of action_type sets."""
    if len(coas) <= 1:
        return 0.0
    total = 0.0
    count = 0
    for i in range(len(coas)):
        for j in range(i + 1, len(coas)):
            set_i = set(a.action_type for a in coas[i].actions)
            set_j = set(a.action_type for a in coas[j].actions)
            union = set_i | set_j
            if not union:
                distance = 0.0
            else:
                intersection = set_i & set_j
                distance = 1.0 - len(intersection) / len(union)
            total += distance
            count += 1
    return total / count if count > 0 else 0.0


def episode_summary(states: List[GameState]) -> Dict:
    """Summarise a completed episode."""
    if not states:
        return {}
    final = states[-1]
    blue_cap = final.blue_capability_total()
    red_cap = final.red_capability_total()
    if blue_cap > red_cap:
        winner = "blue"
    elif red_cap > blue_cap:
        winner = "red"
    else:
        winner = "draw"
    return {
        "n_rounds": len(states) - 1,
        "final_blue_capability": blue_cap,
        "final_red_capability": red_cap,
        "winner": winner,
    }
