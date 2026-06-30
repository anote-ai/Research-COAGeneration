"""Evaluation metrics for coageneration."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, TypeVar

from .core import ActionCategory, CourseOfAction, GameState

T = TypeVar("T")


@dataclass
class BootstrapResult:
    """Percentile-bootstrap confidence interval around a scalar metric.

    Attributes:
        mean: Mean of the bootstrap distribution (not the observed statistic).
        lower: Lower bound of the confidence interval.
        upper: Upper bound of the confidence interval.
        n_boot: Number of bootstrap resamples used.
        confidence: Confidence level (e.g. 0.95 for a 95% CI).
    """

    mean: float
    lower: float
    upper: float
    n_boot: int
    confidence: float

    def __str__(self) -> str:
        pct = int(self.confidence * 100)
        return f"{self.mean:.4f} [{pct}% CI: {self.lower:.4f}–{self.upper:.4f}]"


def bootstrap_ci(
    fn: Callable[[List[T]], float],
    data: List[T],
    n_boot: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Percentile-bootstrap confidence interval for any scalar metric.

    Resamples ``data`` with replacement ``n_boot`` times, applies ``fn`` to
    each resample, and returns percentile-based CI bounds.

    Args:
        fn: A function that takes a list (resample of ``data``) and returns a
            float. Must handle lists of the same element type as ``data``.
        data: The dataset to resample. Must have at least 1 element.
        n_boot: Number of bootstrap iterations. 1000 is standard for 95% CIs;
            use 2000+ for 99% CIs or publication-quality results.
        confidence: Desired confidence level in (0, 1). Default 0.95.
        seed: Random seed for reproducibility.

    Returns:
        A ``BootstrapResult`` with mean, lower, upper, n_boot, confidence.

    Example::

        result = bootstrap_ci(coa_diversity, coas, n_boot=1000)
        print(result)  # "0.6234 [95% CI: 0.5812–0.6641]"
    """
    if not data:
        raise ValueError("data must not be empty")
    if not (0 < confidence < 1):
        raise ValueError("confidence must be in (0, 1)")
    if n_boot < 1:
        raise ValueError("n_boot must be >= 1")

    rng = random.Random(seed)
    n = len(data)
    stats: List[float] = []
    for _ in range(n_boot):
        resample = [data[rng.randint(0, n - 1)] for _ in range(n)]
        stats.append(fn(resample))
    stats.sort()

    alpha = 1.0 - confidence
    lower_idx = max(0, int(alpha / 2 * n_boot))
    upper_idx = min(n_boot - 1, int((1.0 - alpha / 2) * n_boot))
    return BootstrapResult(
        mean=sum(stats) / n_boot,
        lower=stats[lower_idx],
        upper=stats[upper_idx],
        n_boot=n_boot,
        confidence=confidence,
    )


def bootstrap_ci_doctrinal_alignment(
    coas: List[CourseOfAction],
    n_boot: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Bootstrap CI for the mean doctrinal alignment score across a COA set."""

    def _mean_da(sample: List[CourseOfAction]) -> float:
        return sum(doctrinal_alignment_score(c) for c in sample) / len(sample)

    return bootstrap_ci(_mean_da, coas, n_boot=n_boot, confidence=confidence, seed=seed)


def bootstrap_ci_gbc(
    pairs: List[Tuple[CourseOfAction, CourseOfAction]],
    n_boot: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Bootstrap CI for the mean GBC score across (blue, red) COA pairs."""

    def _mean_gbc(sample: List[Tuple[CourseOfAction, CourseOfAction]]) -> float:
        return sum(gbc_score(b, r) for b, r in sample) / len(sample)

    return bootstrap_ci(_mean_gbc, pairs, n_boot=n_boot, confidence=confidence, seed=seed)


def bootstrap_ci_coa_diversity(
    coas: List[CourseOfAction],
    n_boot: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Bootstrap CI for COA diversity (mean pairwise Jaccard distance)."""
    return bootstrap_ci(coa_diversity, coas, n_boot=n_boot, confidence=confidence, seed=seed)


def bootstrap_ci_nash_gap(
    payoff_pairs: List[Tuple[float, float]],
    n_boot: int = 1000,
    confidence: float = 0.95,
    seed: int = 0,
) -> BootstrapResult:
    """Bootstrap CI for the mean Nash gap across (blue_payoff, red_payoff) pairs."""

    def _mean_gap(sample: List[Tuple[float, float]]) -> float:
        return sum(nash_gap(b, r) for b, r in sample) / len(sample)

    return bootstrap_ci(_mean_gap, payoff_pairs, n_boot=n_boot, confidence=confidence, seed=seed)


@dataclass
class CandidateScore:
    """Per-candidate scores within a multi-COA comparison."""

    coa_id: str
    mef_score: float
    doctrinal_alignment: float
    rank: int


@dataclass
class CoaComparison:
    """Comparative analysis across a set of candidate COAs for one scenario.

    Attributes:
        candidates: The COAs that were compared, in input order.
        scores: Per-candidate ``CandidateScore`` entries, ``rank`` 1 = best MEF.
        best: The candidate with the highest MEF score.
        diversity: Mean pairwise Jaccard distance of action types (0 = identical).
        mef_spread: max(mef_score) - min(mef_score) across candidates.
        pareto_optimal_ids: ``coa_id`` of candidates not dominated by any other
            on both (mef_score, doctrinal_alignment) simultaneously.
    """

    candidates: List[CourseOfAction]
    scores: List[CandidateScore]
    best: CourseOfAction
    diversity: float
    mef_spread: float
    pareto_optimal_ids: List[str]


def compare_coas(candidates: List[CourseOfAction]) -> CoaComparison:
    """Compare a set of candidate COAs for the same scenario.

    Ranks candidates by MEF score, computes doctrinal alignment for each,
    measures action-type diversity across the set, and identifies the
    Pareto-optimal subset on (mef_score, doctrinal_alignment) — candidates
    not strictly dominated by any other candidate on both dimensions.

    Args:
        candidates: At least one candidate COA. Typically 3+ for a
            meaningful comparison (e.g. from
            ``SampledBestResponsePolicy.generate_candidates``).

    Returns:
        A ``CoaComparison`` summarising the set.
    """
    if not candidates:
        raise ValueError("candidates must not be empty")

    alignments = [doctrinal_alignment_score(c) for c in candidates]
    order = sorted(
        range(len(candidates)), key=lambda i: candidates[i].mef_score, reverse=True
    )
    ranks = [0] * len(candidates)
    for rank, idx in enumerate(order, start=1):
        ranks[idx] = rank

    scores = [
        CandidateScore(
            coa_id=candidates[i].coa_id,
            mef_score=candidates[i].mef_score,
            doctrinal_alignment=alignments[i],
            rank=ranks[i],
        )
        for i in range(len(candidates))
    ]

    pareto_optimal_ids = []
    for i in range(len(candidates)):
        dominated = False
        for j in range(len(candidates)):
            if i == j:
                continue
            mef_ge = candidates[j].mef_score >= candidates[i].mef_score
            da_ge = alignments[j] >= alignments[i]
            mef_gt = candidates[j].mef_score > candidates[i].mef_score
            da_gt = alignments[j] > alignments[i]
            if mef_ge and da_ge and (mef_gt or da_gt):
                dominated = True
                break
        if not dominated:
            pareto_optimal_ids.append(candidates[i].coa_id)

    mef_values = [c.mef_score for c in candidates]
    return CoaComparison(
        candidates=candidates,
        scores=scores,
        best=candidates[order[0]],
        diversity=coa_diversity(candidates),
        mef_spread=max(mef_values) - min(mef_values),
        pareto_optimal_ids=pareto_optimal_ids,
    )


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
