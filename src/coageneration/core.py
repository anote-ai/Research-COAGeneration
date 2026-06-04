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
    mef_score: float = 0.0
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


def compute_mef_score(
    effectiveness: float,
    cost: float,
    risk: float,
    w_e: float = 0.5,
    w_c: float = 0.3,
    w_r: float = 0.2,
) -> float:
    """Weighted MEF score clamped to [-1, 1]."""
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


class SelfPlayEngine:
    """Alternating self-play between BLUE and RED."""

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self._rng = random.Random(seed)

    def best_response(
        self, coa: CourseOfAction, game_state: GameState
    ) -> CourseOfAction:
        """Generate an adversarial response COA with perturbed actions."""
        response_force = Force.RED if coa.force == Force.BLUE else Force.BLUE
        assets = (
            game_state.red_assets
            if response_force == Force.RED
            else game_state.blue_assets
        )
        categories = list(ActionCategory)
        if not assets:
            response_actions = [
                Action(
                    action_type="hold",
                    asset_id="dummy",
                    priority=1,
                    category=ActionCategory.LOGISTICS,
                )
            ]
        else:
            asset = self._rng.choice(assets)
            response_actions = [
                Action(
                    action_type=self._rng.choice(
                        ["attack", "defend", "maneuver", "recon", "jam", "spoof"]
                    ),
                    category=self._rng.choice(categories),
                    target_location=(
                        self._rng.uniform(0, 100),
                        self._rng.uniform(0, 100),
                    ),
                    asset_id=asset.asset_id,
                    priority=self._rng.randint(1, 10),
                    expected_duration_s=self._rng.uniform(30, 600),
                )
                for _ in range(max(1, len(coa.actions)))
            ]

        effectiveness = self._rng.uniform(0.3, 0.9)
        cost = self._rng.uniform(0.1, 0.5)
        risk = self._rng.uniform(0.1, 0.4)
        mef = compute_mef_score(effectiveness, cost, risk)
        chain = build_chain(response_actions)

        return CourseOfAction(
            force=response_force,
            actions=response_actions,
            chain=chain,
            objective=f"counter: {coa.objective}",
            mef_score=mef,
        )

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
            mef_score=compute_mef_score(
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
