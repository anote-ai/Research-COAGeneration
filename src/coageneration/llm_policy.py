"""LLM-backed COA generation policy using the Anthropic Claude API."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from .core import (
    Action,
    ActionCategory,
    CourseOfAction,
    Force,
    GameState,
    build_chain,
    compute_mef_score,
)

_SYSTEM_PROMPT = """You are a strategic military planning AI. Given a game state and an opponent's Course of Action (COA), generate a tactically sound counter-COA.

Respond with ONLY a JSON object matching this schema (no markdown, no commentary):
{
  "objective": "<string describing your strategic goal>",
  "actions": [
    {
      "action_type": "<one of: attack, defend, maneuver, recon, support, jam, spoof, strike, withdraw, flank, suppress, airlift>",
      "category": "<one of: kinetic, cyber, logistics, intelligence, information>",
      "asset_id": "<asset id from available assets>",
      "priority": <integer 1-10>,
      "target_location": [<x float 0-100>, <y float 0-100>],
      "expected_duration_s": <float seconds>
    }
  ],
  "mef_components": {
    "effectiveness": <float 0-1>,
    "cost": <float 0-1>,
    "risk": <float 0-1>
  }
}

Rules:
- Use only asset_ids from the available assets list.
- Generate between 2 and 5 actions.
- Choose action types and categories that logically counter the opponent's actions.
- effectiveness/cost/risk must reflect the realism of your plan (not just maximise effectiveness).
"""


def _format_state_prompt(
    game_state: GameState,
    opponent_coa: CourseOfAction,
    responding_force: Force,
) -> str:
    available = (
        game_state.red_assets
        if responding_force == Force.RED
        else game_state.blue_assets
    )
    asset_lines = "\n".join(
        f"  - {a.asset_id} ({a.asset_type}) at ({a.location[0]:.1f}, {a.location[1]:.1f}), capability={a.capability_score:.2f}"
        for a in available
    )
    opp_action_lines = "\n".join(
        f"  - [{a.category.value}] {a.action_type} (asset={a.asset_id}, priority={a.priority})"
        for a in opponent_coa.actions
    )
    return (
        f"You are playing as {responding_force.value.upper()}.\n\n"
        f"Available assets:\n{asset_lines}\n\n"
        f"Opponent ({opponent_coa.force.value.upper()}) objective: {opponent_coa.objective}\n"
        f"Opponent actions:\n{opp_action_lines}\n\n"
        f"Generate a counter-COA."
    )


def _parse_llm_response(
    raw: str,
    responding_force: Force,
    game_state: GameState,
) -> CourseOfAction:
    """Parse Claude JSON response into a CourseOfAction, with fallback on parse error."""
    available = (
        game_state.red_assets
        if responding_force == Force.RED
        else game_state.blue_assets
    )
    valid_ids = {a.asset_id for a in available}

    try:
        # Strip any accidental markdown fences
        cleaned = re.sub(r"```[a-z]*\n?", "", raw).strip().rstrip("`")
        data: Dict[str, Any] = json.loads(cleaned)

        actions: List[Action] = []
        for item in data.get("actions", []):
            asset_id = item.get("asset_id", "")
            if asset_id not in valid_ids and valid_ids:
                asset_id = next(iter(valid_ids))

            loc = item.get("target_location")
            target_location = (float(loc[0]), float(loc[1])) if loc and len(loc) == 2 else None

            try:
                category = ActionCategory(item.get("category", "kinetic"))
            except ValueError:
                category = ActionCategory.KINETIC

            actions.append(
                Action(
                    action_type=str(item.get("action_type", "maneuver")),
                    category=category,
                    asset_id=asset_id,
                    priority=max(1, min(10, int(item.get("priority", 5)))),
                    target_location=target_location,
                    expected_duration_s=float(item.get("expected_duration_s", 60.0)),
                )
            )

        mef_c = data.get("mef_components", {})
        mef = compute_mef_score(
            effectiveness=float(mef_c.get("effectiveness", 0.5)),
            cost=float(mef_c.get("cost", 0.3)),
            risk=float(mef_c.get("risk", 0.2)),
        )

        return CourseOfAction(
            force=responding_force,
            actions=actions if actions else _fallback_actions(available),
            chain=build_chain(actions if actions else _fallback_actions(available)),
            objective=str(data.get("objective", "counter opponent COA")),
            mef_score=mef,
        )

    except Exception:
        fallback_actions = _fallback_actions(available)
        return CourseOfAction(
            force=responding_force,
            actions=fallback_actions,
            chain=build_chain(fallback_actions),
            objective="counter opponent COA (fallback)",
            mef_score=compute_mef_score(0.4, 0.3, 0.3),
        )


def _fallback_actions(assets: list) -> List[Action]:
    if not assets:
        return [Action(action_type="hold", asset_id="dummy", category=ActionCategory.LOGISTICS)]
    return [
        Action(
            action_type="defend",
            asset_id=assets[0].asset_id,
            category=ActionCategory.KINETIC,
            priority=5,
        )
    ]


class LLMPolicy:
    """COA generation policy backed by Claude.

    Pass an instance to LLMSelfPlayEngine to replace random best-response
    with strategically reasoned COAs.

    Args:
        client: An ``anthropic.Anthropic`` client instance.
        model: Claude model ID to use.
        max_tokens: Maximum tokens in the response.
    """

    def __init__(
        self,
        client: Any,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1024,
    ) -> None:
        self.client = client
        self.model = model
        self.max_tokens = max_tokens

    def generate_coa(
        self,
        game_state: GameState,
        opponent_coa: CourseOfAction,
        responding_force: Optional[Force] = None,
    ) -> CourseOfAction:
        """Call Claude to generate a counter-COA.

        Args:
            game_state: Current game state with available assets.
            opponent_coa: The COA being responded to.
            responding_force: Which side is responding. Defaults to the
                opposite of opponent_coa.force.
        """
        if responding_force is None:
            responding_force = Force.RED if opponent_coa.force == Force.BLUE else Force.BLUE

        user_prompt = _format_state_prompt(game_state, opponent_coa, responding_force)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        raw = response.content[0].text
        return _parse_llm_response(raw, responding_force, game_state)
