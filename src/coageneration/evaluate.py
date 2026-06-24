"""Evaluation metrics for coageneration."""

from __future__ import annotations

from typing import Dict, List

from .core import ActionCategory, CourseOfAction, GameState


FM30_RUBRIC_WEIGHTS: Dict[str, float] = {
    "objective_clarity": 0.20,
    "intelligence_preparation": 0.18,
    "combined_arms_balance": 0.18,
    "sustainment": 0.14,
    "risk_mitigation": 0.15,
    "tempo_and_sequencing": 0.15,
}


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


def fm30_rubric_scores(coa: CourseOfAction) -> Dict[str, float]:
    """Heuristic FM 3-0 inspired rubric scores in [0, 1].

    This is a benchmark feature extractor, not a substitute for validation by
    doctrine experts. It rewards clear objectives, intelligence preparation,
    combined-arms diversity, sustainment, explicit risk controls, and chained
    sequencing.
    """
    action_types = [atype.lower() for atype in coa.all_action_types()]
    categories = {action.category for action in coa.actions}
    for step in coa.chain:
        if step.action is not None:
            categories.add(step.action.category)
        if step.branch is not None:
            categories.update(action.category for action in step.branch.true_actions)
            categories.update(action.category for action in step.branch.false_actions)

    objective_terms = [term for term in coa.objective.split() if len(term) > 3]
    objective_clarity = min(1.0, len(objective_terms) / 6.0)

    intelligence_terms = {"recon", "scan", "surveillance", "analysis", "assess"}
    intelligence_preparation = 1.0 if (
        ActionCategory.INTELLIGENCE in categories
        or any(any(term in atype for term in intelligence_terms) for atype in action_types)
    ) else 0.0

    combined_arms_balance = min(1.0, len(categories) / 4.0)

    sustainment_terms = {"log", "supply", "resupply", "convoy", "distribute"}
    sustainment = 1.0 if (
        ActionCategory.LOGISTICS in categories
        or any(any(term in atype for term in sustainment_terms) for atype in action_types)
    ) else 0.0

    risk_terms = {"protect", "civilian", "withdraw", "minimum", "restraint", "compliant"}
    risk_mitigation = 1.0 if (
        any(term in coa.objective.lower() for term in risk_terms)
        or any(any(term in atype for term in risk_terms) for atype in action_types)
    ) else min(1.0, len([a for a in coa.actions if a.preconditions]) / 2.0)

    if len(coa.chain) <= 1:
        tempo_and_sequencing = 0.0
    else:
        ordered_steps = sum(1 for step in coa.chain if step.depends_on)
        tempo_and_sequencing = ordered_steps / max(1, len(coa.chain) - 1)

    return {
        "objective_clarity": objective_clarity,
        "intelligence_preparation": intelligence_preparation,
        "combined_arms_balance": combined_arms_balance,
        "sustainment": sustainment,
        "risk_mitigation": risk_mitigation,
        "tempo_and_sequencing": tempo_and_sequencing,
    }


def doctrinal_alignment_score(
    coa: CourseOfAction, weights: Dict[str, float] | None = None
) -> float:
    """Weighted aggregate of ``fm30_rubric_scores`` in [0, 1]."""
    rubric = fm30_rubric_scores(coa)
    active_weights = weights or FM30_RUBRIC_WEIGHTS
    weight_total = sum(active_weights.values())
    if weight_total <= 0:
        return 0.0
    score = sum(rubric.get(key, 0.0) * weight for key, weight in active_weights.items())
    return max(0.0, min(1.0, score / weight_total))


def rubric_inter_rater_agreement(ratings: List[Dict[str, float]]) -> float:
    """Mean pairwise agreement for rubric validator scores in [0, 1]."""
    if len(ratings) <= 1:
        return 1.0
    criteria = sorted({key for rating in ratings for key in rating})
    if not criteria:
        return 0.0
    total = 0.0
    count = 0
    for i in range(len(ratings)):
        for j in range(i + 1, len(ratings)):
            diffs = [
                abs(ratings[i].get(key, 0.0) - ratings[j].get(key, 0.0))
                for key in criteria
            ]
            total += 1.0 - min(1.0, sum(diffs) / len(diffs))
            count += 1
    return total / count if count else 0.0


def framing_sensitivity_delta(frame_scores: Dict[str, float]) -> float:
    """Return max-min score spread across scenario framing variants."""
    if len(frame_scores) <= 1:
        return 0.0
    values = list(frame_scores.values())
    return max(values) - min(values)


def lanchester_wargame_outcome(
    state: GameState,
    blue_coa: CourseOfAction,
    red_coa: CourseOfAction,
    steps: int = 10,
    attrition_rate: float = 0.03,
) -> Dict[str, float | str]:
    """Stylized Lanchester-style outcome linked to COA quality scores."""
    blue = state.blue_capability_total()
    red = state.red_capability_total()
    blue_effect = max(0.05, 1.0 + blue_coa.mef_score + doctrinal_alignment_score(blue_coa))
    red_effect = max(0.05, 1.0 + red_coa.mef_score + doctrinal_alignment_score(red_coa))

    for _ in range(max(0, steps)):
        blue_loss = attrition_rate * red * red_effect
        red_loss = attrition_rate * blue * blue_effect
        blue = max(0.0, blue - blue_loss)
        red = max(0.0, red - red_loss)
        if blue == 0.0 or red == 0.0:
            break

    if blue > red:
        winner = "blue"
    elif red > blue:
        winner = "red"
    else:
        winner = "draw"
    return {
        "blue_remaining": blue,
        "red_remaining": red,
        "blue_doctrinal_alignment": doctrinal_alignment_score(blue_coa),
        "red_doctrinal_alignment": doctrinal_alignment_score(red_coa),
        "winner": winner,
    }


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
