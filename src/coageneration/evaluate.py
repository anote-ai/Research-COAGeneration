"""Evaluation metrics for COA generation."""

from __future__ import annotations

from coageneration.core import CourseOfAction


def gbc_score(blue_coa: CourseOfAction, red_coa: CourseOfAction) -> float:
    """Game-Based COA quality heuristic.

    Returns the normalised advantage of blue over red based on their
    MEF scores: (blue_mef - red_mef + 1) / 2 clamped to [0, 1].
    """
    raw = (blue_coa.mef_score - red_coa.mef_score + 1.0) / 2.0
    return max(0.0, min(1.0, raw))


def nash_gap(blue_payoff: float, red_payoff: float) -> float:
    """Deviation from zero-sum equilibrium: |blue_payoff + red_payoff - 1.0|."""
    return abs(blue_payoff + red_payoff - 1.0)


def robustness_score(
    coa: CourseOfAction,
    adversarial_responses: list[CourseOfAction],
) -> float:
    """Minimum MEF score across adversarial best-responses.

    A robust COA maintains a high MEF even against the worst-case adversary.
    """
    if not adversarial_responses:
        return coa.mef_score
    return min(resp.mef_score for resp in adversarial_responses)


def coa_diversity(coas: list[CourseOfAction]) -> float:
    """Mean pairwise action-set difference (Jaccard distance).

    Returns a value in [0, 1] where 1 means all COAs are completely distinct.
    """
    if len(coas) < 2:
        return 0.0

    distances: list[float] = []
    for i in range(len(coas)):
        for j in range(i + 1, len(coas)):
            set_i = {str(a) for a in coas[i].actions}
            set_j = {str(a) for a in coas[j].actions}
            union = set_i | set_j
            if not union:
                distances.append(0.0)
            else:
                intersection = set_i & set_j
                distances.append(1.0 - len(intersection) / len(union))

    return sum(distances) / len(distances)
