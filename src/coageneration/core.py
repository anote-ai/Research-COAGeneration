"""Core models and game engine for coageneration."""

from __future__ import annotations

import random
import uuid
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class Force(str, Enum):
    BLUE = "blue"
    RED = "red"
    NEUTRAL = "neutral"


class Asset(BaseModel):
    asset_id: str
    asset_type: str
    force: Force
    location: Tuple[float, float]
    capability_score: float = Field(ge=0.0, le=1.0)


class Action(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    action_type: str
    target_location: Optional[Tuple[float, float]] = None
    asset_id: str
    priority: int = 1


class CourseOfAction(BaseModel):
    coa_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    force: Force
    actions: List[Action]
    objective: str
    mef_score: float = 0.0


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
        if not assets:
            # Fallback: create a dummy action
            response_actions = [
                Action(
                    action_type="hold",
                    asset_id="dummy",
                    priority=1,
                )
            ]
        else:
            asset = self._rng.choice(assets)
            response_actions = [
                Action(
                    action_type=self._rng.choice(["attack", "defend", "maneuver", "recon"]),
                    target_location=(
                        self._rng.uniform(0, 100),
                        self._rng.uniform(0, 100),
                    ),
                    asset_id=asset.asset_id,
                    priority=self._rng.randint(1, 5),
                )
                for _ in range(max(1, len(coa.actions)))
            ]

        effectiveness = self._rng.uniform(0.3, 0.9)
        cost = self._rng.uniform(0.1, 0.5)
        risk = self._rng.uniform(0.1, 0.4)
        mef = compute_mef_score(effectiveness, cost, risk)

        return CourseOfAction(
            force=response_force,
            actions=response_actions,
            objective=f"counter: {coa.objective}",
            mef_score=mef,
        )

    def run_episode(
        self, initial_state: GameState, n_rounds: int = 3
    ) -> List[GameState]:
        """Run n_rounds of alternating blue/red moves, return all states."""
        states = [initial_state]
        current_state = initial_state

        # Create a simple initial blue COA
        blue_assets = current_state.blue_assets
        if blue_assets:
            init_action = Action(
                action_type="advance",
                asset_id=blue_assets[0].asset_id,
                priority=1,
            )
        else:
            init_action = Action(action_type="hold", asset_id="dummy")

        current_coa = CourseOfAction(
            force=Force.BLUE,
            actions=[init_action],
            objective="neutralize red",
            mef_score=compute_mef_score(
                self._rng.uniform(0.4, 0.9),
                self._rng.uniform(0.1, 0.4),
                self._rng.uniform(0.1, 0.3),
            ),
        )

        for round_i in range(n_rounds):
            # Adversary responds
            response_coa = self.best_response(current_coa, current_state)

            # Evolve state: capabilities shift slightly
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
