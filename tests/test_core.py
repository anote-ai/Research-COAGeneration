"""Tests for coageneration.core."""

import pytest
from coageneration.core import (
    Action,
    Asset,
    CourseOfAction,
    Force,
    GameState,
    SelfPlayEngine,
    compute_mef_score,
)


def _asset(force=Force.BLUE, cap=0.8, aid="a1"):
    return Asset(
        asset_id=aid,
        asset_type="infantry",
        force=force,
        location=(10.0, 20.0),
        capability_score=cap,
    )


def _action(asset_id="a1", action_type="attack"):
    return Action(action_type=action_type, asset_id=asset_id)


def _coa(force=Force.BLUE, n=2):
    actions = [_action(f"a{i}") for i in range(n)]
    return CourseOfAction(force=force, actions=actions, objective="test", mef_score=0.5)


def _state(n_blue=3, n_red=3):
    blue = [_asset(Force.BLUE, 0.8, f"b{i}") for i in range(n_blue)]
    red = [_asset(Force.RED, 0.6, f"r{i}") for i in range(n_red)]
    return GameState(blue_assets=blue, red_assets=red)


def test_force_enum():
    assert Force.BLUE == "blue"
    assert Force.RED == "red"
    assert Force.NEUTRAL == "neutral"


def test_asset_construction():
    a = _asset()
    assert a.capability_score == pytest.approx(0.8)
    assert a.force == Force.BLUE


def test_action_default_id():
    a = _action()
    assert isinstance(a.action_id, str)
    assert len(a.action_id) == 8


def test_course_of_action_fields():
    coa = _coa(n=3)
    assert len(coa.actions) == 3
    assert coa.mef_score == pytest.approx(0.5)


def test_game_state_blue_capability_total():
    state = _state(n_blue=3, n_red=0)
    assert state.blue_capability_total() == pytest.approx(0.8 * 3)


def test_game_state_red_capability_total():
    state = _state(n_blue=0, n_red=4)
    assert state.red_capability_total() == pytest.approx(0.6 * 4)


def test_compute_mef_score_known():
    score = compute_mef_score(effectiveness=1.0, cost=0.0, risk=0.0)
    assert score == pytest.approx(0.5)


def test_compute_mef_score_clamped():
    score = compute_mef_score(effectiveness=10.0, cost=0.0, risk=0.0)
    assert score == pytest.approx(1.0)
    score2 = compute_mef_score(effectiveness=0.0, cost=10.0, risk=10.0)
    assert score2 == pytest.approx(-1.0)


def test_self_play_engine_best_response():
    engine = SelfPlayEngine(seed=42)
    coa = _coa(force=Force.BLUE)
    state = _state()
    response = engine.best_response(coa, state)
    assert isinstance(response, CourseOfAction)
    assert response.force == Force.RED


def test_run_episode_length():
    engine = SelfPlayEngine(seed=42)
    state = _state()
    n_rounds = 4
    states = engine.run_episode(state, n_rounds=n_rounds)
    assert len(states) == n_rounds + 1
