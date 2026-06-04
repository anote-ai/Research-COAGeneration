"""Factory helpers for coageneration."""

from __future__ import annotations

import random
from typing import List

from .core import Action, Asset, CourseOfAction, Force, GameState, compute_mef_score


def make_asset(
    force: Force = Force.BLUE,
    capability: float = 0.8,
    asset_id: str = "asset-001",
    asset_type: str = "infantry",
    location: tuple = (10.0, 20.0),
) -> Asset:
    return Asset(
        asset_id=asset_id,
        asset_type=asset_type,
        force=force,
        location=location,
        capability_score=capability,
    )


def make_action(
    asset_id: str = "a1",
    action_type: str = "attack",
    target_location: tuple = (50.0, 50.0),
    priority: int = 1,
) -> Action:
    return Action(
        action_type=action_type,
        target_location=target_location,
        asset_id=asset_id,
        priority=priority,
    )


def make_coa(
    force: Force = Force.BLUE,
    n_actions: int = 3,
    objective: str = "neutralize red",
    seed: int = 42,
) -> CourseOfAction:
    rng = random.Random(seed)
    action_types = ["attack", "defend", "maneuver", "recon", "support"]
    actions = [
        Action(
            action_type=rng.choice(action_types),
            target_location=(rng.uniform(0, 100), rng.uniform(0, 100)),
            asset_id=f"asset-{i:03d}",
            priority=rng.randint(1, 5),
        )
        for i in range(n_actions)
    ]
    mef = compute_mef_score(
        effectiveness=rng.uniform(0.5, 1.0),
        cost=rng.uniform(0.1, 0.5),
        risk=rng.uniform(0.05, 0.3),
    )
    return CourseOfAction(
        force=force,
        actions=actions,
        objective=objective,
        mef_score=mef,
    )


def make_game_state(
    n_blue: int = 5,
    n_red: int = 5,
    seed: int = 42,
) -> GameState:
    rng = random.Random(seed)
    blue_asset_types = ["infantry", "armor", "artillery", "air", "naval"]
    red_asset_types = ["infantry", "armor", "artillery", "air", "naval"]

    blue_assets = [
        Asset(
            asset_id=f"blue-{i:03d}",
            asset_type=blue_asset_types[i % len(blue_asset_types)],
            force=Force.BLUE,
            location=(rng.uniform(0, 50), rng.uniform(0, 100)),
            capability_score=rng.uniform(0.5, 1.0),
        )
        for i in range(n_blue)
    ]
    red_assets = [
        Asset(
            asset_id=f"red-{i:03d}",
            asset_type=red_asset_types[i % len(red_asset_types)],
            force=Force.RED,
            location=(rng.uniform(50, 100), rng.uniform(0, 100)),
            capability_score=rng.uniform(0.5, 1.0),
        )
        for i in range(n_red)
    ]
    return GameState(blue_assets=blue_assets, red_assets=red_assets, turn=0)
