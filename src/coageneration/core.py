"""Core models and generation engine for coageneration."""

from __future__ import annotations

import random
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class Force(str, Enum):
    BLUE = "blue"
    RED = "red"
    NEUTRAL = "neutral"


class ActionCategory(str, Enum):
    KINETIC = "kinetic"
    CYBER = "cyber"
    LOGISTICS = "logistics"
    INTELLIGENCE = "intelligence"
    INFORMATION = "information"


class Asset(BaseModel):
    asset_id: str
    asset_type: str
    force: Force
    location: Tuple[float, float]
    capability_score: float = Field(ge=0.0, le=1.0)


class ToolCall(BaseModel):
    """Typed tool invocation attached to an action."""

    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    expected_output_type: str = "any"


class Action(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: str
    category: ActionCategory = ActionCategory.KINETIC
    target_location: Optional[Tuple[float, float]] = None
    asset_id: str
    priority: int = Field(default=1, ge=1, le=10)
    tool_call: Optional[ToolCall] = None
    preconditions: List[str] = Field(default_factory=list)
    expected_duration_s: float = Field(default=60.0, ge=0.0)


class ConditionalBranch(BaseModel):
    """A conditional branch within a chain-of-action."""

    condition: str
    true_actions: List[Action]
    false_actions: List[Action]


class ChainStep(BaseModel):
    """One step in a multi-step CoA chain."""

    step_index: int
    action: Optional[Action] = None
    branch: Optional[ConditionalBranch] = None
    depends_on: List[int] = Field(default_factory=list)

    @field_validator("step_index")
    @classmethod
    def non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("step_index must be >= 0")
        return v


class CourseOfAction(BaseModel):
    coa_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    force: Force
    actions: List[Action]
    chain: List[ChainStep] = Field(default_factory=list)
    objective: str
    quality_score: float = 0.0
    domain: str = "military"

    def all_action_types(self) -> List[str]:
        """Return action types from flat actions and chain steps."""
        types = [a.action_type for a in self.actions]
        for step in self.chain:
            if step.action is not None:
                types.append(step.action.action_type)
            if step.branch is not None:
                types.extend(a.action_type for a in step.branch.true_actions)
                types.extend(a.action_type for a in step.branch.false_actions)
        return types

    def unique_tool_names(self) -> List[str]:
        """Collect distinct tool names used across all actions."""
        names: List[str] = []
        for action in self.actions:
            if action.tool_call is not None:
                names.append(action.tool_call.tool_name)
        for step in self.chain:
            if step.action is not None and step.action.tool_call is not None:
                names.append(step.action.tool_call.tool_name)
        return list(dict.fromkeys(names))


class GameState(BaseModel):
    state_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    blue_assets: List[Asset]
    red_assets: List[Asset]
    turn: int = 0

    def blue_capability_total(self) -> float:
        return sum(a.capability_score for a in self.blue_assets)

    def red_capability_total(self) -> float:
        return sum(a.capability_score for a in self.red_assets)


class ScenarioProfile(BaseModel):
    """Metadata describing a synthetic evaluation scenario."""

    scenario_id: str
    terrain_type: str
    force_size: str
    operational_phase: str
    domains: List[str]
    framing: str = "neutral"
    loac_ambiguity: str = "low"
    historical_reference: Optional[str] = None


class ScenarioCase(BaseModel):
    """A reproducible scenario bundle for COA evaluation."""

    profile: ScenarioProfile
    game_state: GameState
    seed_coas: List[CourseOfAction] = Field(default_factory=list)


class MultiAgentCouncilResult(BaseModel):
    """Trace emitted by the multi-agent COA council algorithm."""

    blue_candidates: List[CourseOfAction]
    revised_candidates: List[CourseOfAction] = Field(default_factory=list)
    selected_blue: CourseOfAction
    selected_red: CourseOfAction
    candidate_scores: Dict[str, float]
    candidate_pressures: Dict[str, float] = Field(default_factory=dict)
    round_index: Dict[str, int] = Field(default_factory=dict)
    consensus_gap: float
    adversarial_pressure: float
    robustness_margin: float = 0.0
    pressure_reduction: float = 0.0


def compute_quality_score(
    effectiveness: float,
    cost: float,
    risk: float,
    w_e: float = 0.5,
    w_c: float = 0.3,
    w_r: float = 0.2,
) -> float:
    """Internal synthetic COA quality score clamped to [-1, 1]."""
    raw = w_e * effectiveness - w_c * cost - w_r * risk
    return max(-1.0, min(1.0, raw))


def build_chain(
    actions: List[Action],
    linear: bool = True,
) -> List[ChainStep]:
    """Build a ChainStep list from a flat action list.

    When ``linear=True`` each step depends on the immediately preceding step,
    creating a sequential chain.  Otherwise steps have no explicit dependencies
    (parallel execution is implied).
    """
    steps: List[ChainStep] = []
    for i, action in enumerate(actions):
        depends = [i - 1] if (linear and i > 0) else []
        steps.append(ChainStep(step_index=i, action=action, depends_on=depends))
    return steps


_RESPONSE_ACTION_TYPES = ["attack", "defend", "maneuver", "recon", "jam", "spoof"]


def _random_response_coa(
    opponent_coa: "CourseOfAction",
    game_state: "GameState",
    responding_force: "Force",
    rng: random.Random,
) -> "CourseOfAction":
    """Generate a single random counter-COA for ``responding_force``."""
    assets = (
        game_state.red_assets
        if responding_force == Force.RED
        else game_state.blue_assets
    )
    categories = list(ActionCategory)
    if not assets:
        actions = [
            Action(
                action_type="hold",
                asset_id="dummy",
                priority=1,
                category=ActionCategory.LOGISTICS,
            )
        ]
    else:
        asset = rng.choice(assets)
        actions = [
            Action(
                action_type=rng.choice(_RESPONSE_ACTION_TYPES),
                category=rng.choice(categories),
                target_location=(rng.uniform(0, 100), rng.uniform(0, 100)),
                asset_id=asset.asset_id,
                priority=rng.randint(1, 10),
                expected_duration_s=rng.uniform(30, 600),
            )
            for _ in range(max(1, len(opponent_coa.actions)))
        ]

    quality = compute_quality_score(
        rng.uniform(0.3, 0.9),
        rng.uniform(0.1, 0.5),
        rng.uniform(0.1, 0.4),
    )
    return CourseOfAction(
        force=responding_force,
        actions=actions,
        chain=build_chain(actions),
        objective=f"counter: {opponent_coa.objective}",
        quality_score=quality,
    )


class Policy:
    """Abstract interface for a COA generation policy."""

    def generate_coa(
        self, game_state: "GameState", opponent_coa: "CourseOfAction"
    ) -> "CourseOfAction":
        raise NotImplementedError


class SampledBestResponsePolicy(Policy):
    """Sample ``n_samples`` random COAs and return the highest quality one.

    This is a substantial improvement over single-sample random play: by
    evaluating multiple candidates and selecting the best, the responding
    force behaves more like a greedy optimizer than a coin-flip — tightening
    the self-play loop and making Nash-gap convergence meaningful.

    Args:
        n_samples: Number of candidate COAs to generate per call. Higher
            values give better best-response approximations at the cost of
            more computation. Default is 8.
        seed: Random seed for reproducibility.
    """

    def __init__(self, n_samples: int = 8, seed: int = 0) -> None:
        if n_samples < 1:
            raise ValueError("n_samples must be >= 1")
        self.n_samples = n_samples
        self._rng = random.Random(seed)

    def generate_candidates(
        self, game_state: "GameState", opponent_coa: "CourseOfAction"
    ) -> List["CourseOfAction"]:
        """Generate ``n_samples`` distinct candidate COAs without selecting one.

        Useful for surfacing multi-COA comparisons (see ``evaluate.compare_coas``)
        rather than only ever seeing the single best-response winner.
        """
        responding_force = (
            Force.RED if opponent_coa.force == Force.BLUE else Force.BLUE
        )
        return [
            _random_response_coa(opponent_coa, game_state, responding_force, self._rng)
            for _ in range(self.n_samples)
        ]

    def generate_coa(
        self, game_state: "GameState", opponent_coa: "CourseOfAction"
    ) -> "CourseOfAction":
        candidates = self.generate_candidates(game_state, opponent_coa)
        return max(candidates, key=lambda c: c.quality_score)


def _doctrine_proxy_score(coa: CourseOfAction) -> float:
    """Lightweight doctrine proxy used inside core policy selection.

    The full FM 3-0-inspired rubric lives in ``coageneration.evaluate``.
    Keeping this proxy local avoids a circular dependency while allowing a
    response policy to trade off synthetic quality against inspectable plan
    structure: category coverage, sequencing, preconditions, and risk language.
    """
    categories = {action.category for action in coa.actions}
    for step in coa.chain:
        if step.action is not None:
            categories.add(step.action.category)
        if step.branch is not None:
            categories.update(action.category for action in step.branch.true_actions)
            categories.update(action.category for action in step.branch.false_actions)

    category_coverage = min(1.0, len(categories) / 4.0)
    sequencing = 0.0
    if len(coa.chain) > 1:
        sequencing = sum(1 for step in coa.chain if step.depends_on) / max(
            1, len(coa.chain) - 1
        )
    guarded_actions = sum(1 for action in coa.actions if action.preconditions)
    precondition_coverage = min(1.0, guarded_actions / max(1, len(coa.actions)))
    risk_terms = {"protect", "civilian", "withdraw", "minimum", "restraint", "compliant"}
    risk_language = 1.0 if any(term in coa.objective.lower() for term in risk_terms) else 0.0
    return (
        0.35 * category_coverage
        + 0.30 * sequencing
        + 0.20 * precondition_coverage
        + 0.15 * risk_language
    )


class DoctrineAwareBestResponsePolicy(SampledBestResponsePolicy):
    """Sample candidates and select by quality plus a doctrine proxy.

    ``SampledBestResponsePolicy`` is deliberately quality-greedy. This variant
    models a richer baseline where an adversary does not simply maximize the
    synthetic quality score, but also prefers better-structured, more coherent
    COAs. The selected candidate maximizes::

        quality_weight * q + doctrine_weight * d

    where ``q`` is rescaled to [0, 1] and ``d`` is the local doctrine proxy.
    """

    def __init__(
        self,
        n_samples: int = 8,
        seed: int = 0,
        quality_weight: float = 0.7,
        doctrine_weight: float = 0.3,
    ) -> None:
        super().__init__(n_samples=n_samples, seed=seed)
        if quality_weight < 0 or doctrine_weight < 0:
            raise ValueError("weights must be non-negative")
        if quality_weight + doctrine_weight <= 0:
            raise ValueError("at least one weight must be positive")
        self.quality_weight = quality_weight
        self.doctrine_weight = doctrine_weight

    def candidate_score(self, coa: CourseOfAction) -> float:
        quality = (coa.quality_score + 1.0) / 2.0
        doctrine = _doctrine_proxy_score(coa)
        total = self.quality_weight + self.doctrine_weight
        return (
            self.quality_weight * quality + self.doctrine_weight * doctrine
        ) / total

    def generate_coa(
        self, game_state: "GameState", opponent_coa: "CourseOfAction"
    ) -> "CourseOfAction":
        candidates = self.generate_candidates(game_state, opponent_coa)
        return max(candidates, key=self.candidate_score)


class MultiAgentCouncilPolicy:
    """Generate BLUE COAs with proposer agents and select via RED-team pressure.

    The council simulates a small multi-agent planning loop:

    * BLUE proposer agents create role-specialized COA variants.
    * RED-team agents sample adversarial responses for every BLUE candidate.
    * An adjudicator shortlists candidates with the best composite score.
    * A deliberation step revises shortlisted COAs with mitigation actions.
    * The adjudicator selects the final BLUE candidate after a second stress test.

    This is intentionally lightweight and deterministic enough for offline
    benchmarking; it is a scaffold for comparing multi-agent COA generation
    algorithms, not an operational planning system.
    """

    _ROLE_ACTIONS: Dict[str, Tuple[str, ActionCategory, float]] = {
        "maneuver": ("flank_and_fix", ActionCategory.KINETIC, 0.030),
        "intelligence": ("persistent_surveillance", ActionCategory.INTELLIGENCE, 0.025),
        "cyber": ("disrupt_command_links", ActionCategory.CYBER, 0.020),
        "sustainment": ("forward_resupply_node", ActionCategory.LOGISTICS, 0.018),
        "protection": ("civilian_harm_mitigation", ActionCategory.INFORMATION, 0.015),
    }

    def __init__(
        self,
        proposer_roles: List[str] | None = None,
        red_team_samples: int = 4,
        seed: int = 0,
        quality_weight: float = 0.45,
        doctrine_weight: float = 0.25,
        diversity_weight: float = 0.10,
        pressure_weight: float = 0.20,
        deliberation_width: int = 2,
        revision_bonus: float = 0.025,
    ) -> None:
        if red_team_samples < 1:
            raise ValueError("red_team_samples must be >= 1")
        if deliberation_width < 1:
            raise ValueError("deliberation_width must be >= 1")
        self.proposer_roles = proposer_roles or [
            "maneuver",
            "intelligence",
            "cyber",
            "sustainment",
            "protection",
        ]
        unknown = [role for role in self.proposer_roles if role not in self._ROLE_ACTIONS]
        if unknown:
            raise ValueError(f"unknown proposer roles: {unknown}")
        weights = [quality_weight, doctrine_weight, diversity_weight, pressure_weight]
        if any(weight < 0 for weight in weights):
            raise ValueError("weights must be non-negative")
        if sum(weights) <= 0:
            raise ValueError("at least one weight must be positive")
        self.red_team_samples = red_team_samples
        self._rng = random.Random(seed)
        self.quality_weight = quality_weight
        self.doctrine_weight = doctrine_weight
        self.diversity_weight = diversity_weight
        self.pressure_weight = pressure_weight
        self.deliberation_width = deliberation_width
        self.revision_bonus = revision_bonus

    def _role_variant(
        self, seed_coa: CourseOfAction, role: str, idx: int
    ) -> CourseOfAction:
        action_type, category, quality_bonus = self._ROLE_ACTIONS[role]
        base_actions = [
            action.model_copy(deep=True)
            for action in seed_coa.actions
        ]
        asset_id = base_actions[0].asset_id if base_actions else f"council-{role}-asset"
        role_action = Action(
            action_type=action_type,
            category=category,
            asset_id=asset_id,
            priority=min(10, 1 + idx),
            preconditions=["council_review_complete"],
            expected_duration_s=90.0 + 15.0 * idx,
        )
        actions = base_actions + [role_action]
        jitter = self._rng.uniform(-0.015, 0.015)
        return CourseOfAction(
            force=Force.BLUE,
            actions=actions,
            chain=build_chain(actions),
            objective=f"{seed_coa.objective}; {role} proposer refinement",
            quality_score=max(-1.0, min(1.0, seed_coa.quality_score + quality_bonus + jitter)),
            domain=seed_coa.domain,
        )

    def generate_blue_candidates(
        self, seed_coas: List[CourseOfAction]
    ) -> List[CourseOfAction]:
        if not seed_coas:
            raise ValueError("seed_coas must not be empty")
        candidates: List[CourseOfAction] = []
        for i, role in enumerate(self.proposer_roles):
            seed_coa = seed_coas[i % len(seed_coas)]
            candidates.append(self._role_variant(seed_coa, role, i))
        return candidates

    def _jaccard_distance(self, own_types: set[str], other_types: set[str]) -> float:
        if not own_types and not other_types:
            return 0.0
        return 1.0 - len(own_types & other_types) / len(own_types | other_types)

    def _score_candidate(
        self,
        candidate: CourseOfAction,
        selected_red: CourseOfAction,
        own_types: set[str],
        other_types: set[str],
    ) -> Tuple[float, float]:
        quality = (candidate.quality_score + 1.0) / 2.0
        doctrine = _doctrine_proxy_score(candidate)
        pressure = (selected_red.quality_score + 1.0) / 2.0
        diversity = self._jaccard_distance(own_types, other_types)
        score = (
            self.quality_weight * quality
            + self.doctrine_weight * doctrine
            + self.diversity_weight * diversity
            - self.pressure_weight * pressure
        )
        return score, pressure

    def _revise_candidate(
        self,
        candidate: CourseOfAction,
        selected_red: CourseOfAction,
        round_idx: int,
    ) -> CourseOfAction:
        """Revise a candidate after RED-team critique.

        The revision is deliberately simple and inspectable: it adds a
        mitigation action keyed to the strongest RED response category and
        slightly increases synthetic quality to represent risk reduction.
        """
        mitigation_by_category = {
            ActionCategory.KINETIC: ("dispersion_and_hardening", ActionCategory.LOGISTICS),
            ActionCategory.CYBER: ("out_of_band_comms", ActionCategory.CYBER),
            ActionCategory.LOGISTICS: ("redundant_supply_route", ActionCategory.LOGISTICS),
            ActionCategory.INTELLIGENCE: (
                "deception_and_counter_recon",
                ActionCategory.INFORMATION,
            ),
            ActionCategory.INFORMATION: (
                "public_information_cell",
                ActionCategory.INFORMATION,
            ),
        }
        red_category = selected_red.actions[0].category if selected_red.actions else ActionCategory.KINETIC
        action_type, category = mitigation_by_category[red_category]
        actions = [action.model_copy(deep=True) for action in candidate.actions]
        asset_id = actions[0].asset_id if actions else "council-revision-asset"
        mitigation = Action(
            action_type=f"{action_type}_r{round_idx}",
            category=category,
            asset_id=asset_id,
            priority=8,
            preconditions=["red_team_critique_received"],
            expected_duration_s=120.0,
        )
        actions.append(mitigation)
        return CourseOfAction(
            force=Force.BLUE,
            actions=actions,
            chain=build_chain(actions),
            objective=f"{candidate.objective}; revised against {selected_red.actions[0].action_type if selected_red.actions else 'red pressure'}",
            quality_score=max(-1.0, min(1.0, candidate.quality_score + self.revision_bonus)),
            domain=candidate.domain,
        )

    def _evaluate_candidates(
        self,
        candidates: List[CourseOfAction],
        game_state: GameState,
        red_policy: SampledBestResponsePolicy,
        round_number: int,
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, CourseOfAction], Dict[str, int]]:
        scores: Dict[str, float] = {}
        pressures: Dict[str, float] = {}
        selected_red_by_blue: Dict[str, CourseOfAction] = {}
        round_index: Dict[str, int] = {}
        action_type_sets = [set(candidate.all_action_types()) for candidate in candidates]

        for i, candidate in enumerate(candidates):
            red_candidates = red_policy.generate_candidates(game_state, candidate)
            selected_red = max(red_candidates, key=lambda c: c.quality_score)
            selected_red_by_blue[candidate.coa_id] = selected_red
            other_types = set().union(
                *(types for j, types in enumerate(action_type_sets) if j != i)
            )
            score, pressure = self._score_candidate(
                candidate, selected_red, action_type_sets[i], other_types
            )
            scores[candidate.coa_id] = score
            pressures[candidate.coa_id] = pressure
            round_index[candidate.coa_id] = round_number
        return scores, pressures, selected_red_by_blue, round_index

    def run_council(
        self, game_state: GameState, seed_coas: List[CourseOfAction]
    ) -> MultiAgentCouncilResult:
        candidates = self.generate_blue_candidates(seed_coas)
        red_policy = SampledBestResponsePolicy(
            n_samples=self.red_team_samples,
            seed=self._rng.randint(0, 10_000_000),
        )
        candidate_scores, candidate_pressures, selected_red_by_blue, round_index = (
            self._evaluate_candidates(candidates, game_state, red_policy, round_number=0)
        )

        first_round_order = sorted(
            candidate_scores.items(), key=lambda item: item[1], reverse=True
        )
        shortlist = [
            next(c for c in candidates if c.coa_id == candidate_id)
            for candidate_id, _ in first_round_order[: self.deliberation_width]
        ]
        revised_candidates = [
            self._revise_candidate(
                candidate,
                selected_red_by_blue[candidate.coa_id],
                round_idx=idx + 1,
            )
            for idx, candidate in enumerate(shortlist)
        ]
        (
            revised_scores,
            revised_pressures,
            revised_red_by_blue,
            revised_round_index,
        ) = self._evaluate_candidates(
            revised_candidates, game_state, red_policy, round_number=1
        )
        candidate_scores.update(revised_scores)
        candidate_pressures.update(revised_pressures)
        selected_red_by_blue.update(revised_red_by_blue)
        round_index.update(revised_round_index)

        ordered = sorted(candidate_scores.items(), key=lambda item: item[1], reverse=True)
        selected_blue_id = ordered[0][0]
        all_blue_candidates = candidates + revised_candidates
        selected_blue = next(c for c in all_blue_candidates if c.coa_id == selected_blue_id)
        selected_red = selected_red_by_blue[selected_blue_id]
        consensus_gap = ordered[0][1] - ordered[1][1] if len(ordered) > 1 else ordered[0][1]
        adversarial_pressure = candidate_pressures[selected_blue_id]
        round_zero_scores = [
            score
            for candidate_id, score in candidate_scores.items()
            if round_index[candidate_id] == 0
        ]
        robustness_margin = (
            ordered[0][1] - max(round_zero_scores)
            if round_zero_scores
            else consensus_gap
        )
        initial_shortlist_pressure = sum(
            candidate_pressures[candidate.coa_id] for candidate in shortlist
        ) / len(shortlist)
        pressure_reduction = initial_shortlist_pressure - adversarial_pressure
        return MultiAgentCouncilResult(
            blue_candidates=candidates,
            revised_candidates=revised_candidates,
            selected_blue=selected_blue,
            selected_red=selected_red,
            candidate_scores=candidate_scores,
            candidate_pressures=candidate_pressures,
            round_index=round_index,
            consensus_gap=consensus_gap,
            adversarial_pressure=adversarial_pressure,
            robustness_margin=robustness_margin,
            pressure_reduction=pressure_reduction,
        )


class SelfPlayEngine:
    """Alternating self-play between BLUE and RED.

    Pass a ``policy`` to replace the built-in single-sample random best-response
    with any ``Policy``-compatible object (e.g. ``SampledBestResponsePolicy``
    or ``LLMPolicy``).
    """

    def __init__(self, seed: int = 42, policy: Optional[Policy] = None) -> None:
        self.seed = seed
        self._rng = random.Random(seed)
        self.policy = policy

    def best_response(
        self, coa: CourseOfAction, game_state: GameState
    ) -> CourseOfAction:
        """Generate an adversarial response COA.

        Delegates to ``self.policy`` if one was provided; otherwise falls back
        to a single random sample.
        """
        if self.policy is not None:
            return self.policy.generate_coa(game_state, coa)

        response_force = Force.RED if coa.force == Force.BLUE else Force.BLUE
        return _random_response_coa(coa, game_state, response_force, self._rng)

    def run_episode(
        self, initial_state: GameState, n_rounds: int = 3
    ) -> List[GameState]:
        """Run n_rounds of alternating blue/red moves, return all states."""
        states = [initial_state]
        current_state = initial_state

        blue_assets = current_state.blue_assets
        if blue_assets:
            init_action = Action(
                action_type="advance",
                asset_id=blue_assets[0].asset_id,
                priority=1,
                category=ActionCategory.KINETIC,
            )
        else:
            init_action = Action(
                action_type="hold",
                asset_id="dummy",
                category=ActionCategory.LOGISTICS,
            )

        current_coa = CourseOfAction(
            force=Force.BLUE,
            actions=[init_action],
            chain=build_chain([init_action]),
            objective="neutralize red",
            quality_score=compute_quality_score(
                self._rng.uniform(0.4, 0.9),
                self._rng.uniform(0.1, 0.4),
                self._rng.uniform(0.1, 0.3),
            ),
        )

        for _round_i in range(n_rounds):
            response_coa = self.best_response(current_coa, current_state)

            new_blue = [
                Asset(
                    asset_id=a.asset_id,
                    asset_type=a.asset_type,
                    force=a.force,
                    location=a.location,
                    capability_score=max(
                        0.0,
                        min(1.0, a.capability_score - self._rng.uniform(0, 0.05)),
                    ),
                )
                for a in current_state.blue_assets
            ]
            new_red = [
                Asset(
                    asset_id=a.asset_id,
                    asset_type=a.asset_type,
                    force=a.force,
                    location=a.location,
                    capability_score=max(
                        0.0,
                        min(1.0, a.capability_score - self._rng.uniform(0, 0.05)),
                    ),
                )
                for a in current_state.red_assets
            ]
            next_state = GameState(
                blue_assets=new_blue,
                red_assets=new_red,
                turn=current_state.turn + 1,
            )
            states.append(next_state)
            current_state = next_state
            current_coa = response_coa

        return states
