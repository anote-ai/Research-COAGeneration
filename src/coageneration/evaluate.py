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


def chain_coverage_score(coas: List[CourseOfAction]) -> float:
    """Fraction of COAs that have a non-empty multi-step chain.

    A higher score means the dataset captures chained / sequential
    reasoning rather than single flat actions.
    """
    if not coas:
        return 0.0
    with_chain = sum(1 for c in coas if len(c.chain) > 1)
    return with_chain / len(coas)


def action_diversity_score(coas: List[CourseOfAction]) -> float:
    """Normalised entropy of action-type distribution across all COAs.

    Returns a value in [0, 1] where 1 means perfectly uniform distribution
    over action types (maximum diversity) and 0 means all actions are identical.
    """
    import math

    counts: Dict[str, int] = {}
    for coa in coas:
        for atype in coa.all_action_types():
            counts[atype] = counts.get(atype, 0) + 1
    total = sum(counts.values())
    if total == 0:
        return 0.0
    n_types = len(counts)
    if n_types <= 1:
        return 0.0
    entropy = -sum(
        (c / total) * math.log(c / total) for c in counts.values() if c > 0
    )
    max_entropy = math.log(n_types)
    return entropy / max_entropy if max_entropy > 0 else 0.0


def tool_utilisation_rate(coas: List[CourseOfAction]) -> float:
    """Fraction of actions across all COAs that carry a tool call."""
    total_actions = 0
    tool_actions = 0
    for coa in coas:
        for action in coa.actions:
            total_actions += 1
            if action.tool_call is not None:
                tool_actions += 1
    if total_actions == 0:
        return 0.0
    return tool_actions / total_actions


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
