"""Core data models and algorithms for COA generation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Force(str, Enum):
    BLUE = "blue"
    RED = "red"
    NEUTRAL = "neutral"


class Asset(BaseModel):
    asset_id: str
    asset_type: str
    force: Force
    location: tuple[float, float]
    capability_score: float = Field(ge=0.0, le=1.0)


class CourseOfAction(BaseModel):
    coa_id: str
    force: Force
    actions: list[dict[str, Any]]
    objective: str
    mef_score: float = 0.0


class GameState(BaseModel):
    state_id: str
    blue_assets: list[Asset]
    red_assets: list[Asset]
    turn: int = Field(ge=0)


@dataclass
class MEFScore:
    coa_id: str
    effectiveness: float
    cost: float
    risk: float
    composite: float


def compute_mef_score(
    effectiveness: float,
    cost: float,
    risk: float,
    w_e: float = 0.5,
    w_c: float = 0.3,
    w_r: float = 0.2,
) -> float:
    """Weighted composite MEF score.

    Higher effectiveness is better; lower cost and risk are better.
    Score = w_e * effectiveness - w_c * cost - w_r * risk
    """
    return w_e * effectiveness - w_c * cost - w_r * risk


class SelfPlayEngine:
    """Game-theoretic self-play engine for COA generation."""

    def best_response(
        self,
        coa: CourseOfAction,
        game_state: GameState,
    ) -> CourseOfAction:
        """Return a best-response COA for the opposing force (stub).

        In a full implementation this would invoke an LLM or search
        algorithm to generate an adversarial best response.
        """
        opposing_force = Force.RED if coa.force == Force.BLUE else Force.BLUE
        return CourseOfAction(
            coa_id=f"br-{coa.coa_id}",
            force=opposing_force,
            actions=[],
            objective="counter " + coa.objective,
            mef_score=0.0,
        )

    def run_episode(self, n_rounds: int) -> list[GameState]:
        """Run a self-play episode for n_rounds and return game states (stub)."""
        return [
            GameState(
                state_id=f"state-{r}",
                blue_assets=[],
                red_assets=[],
                turn=r,
            )
            for r in range(n_rounds)
        ]
