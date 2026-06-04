"""Tests for coageneration.core."""

import pytest

from coageneration.core import (
    Asset,
    CourseOfAction,
    Force,
    GameState,
    MEFScore,
    SelfPlayEngine,
    compute_mef_score,
)


def test_force_enum_values():
    assert Force.BLUE == "blue"
    assert Force.RED == "red"
    assert Force.NEUTRAL == "neutral"


def test_asset_construction():
    asset = Asset(
        asset_id="a1",
        asset_type="tank",
        force=Force.BLUE,
        location=(34.5, -117.2),
        capability_score=0.8,
    )
    assert asset.force == Force.BLUE
    assert asset.location == (34.5, -117.2)


def test_course_of_action_construction():
    coa = CourseOfAction(
        coa_id="coa-1",
        force=Force.RED,
        actions=[{"type": "advance", "target": "obj-A"}],
        objective="Capture objective A",
        mef_score=0.72,
    )
    assert coa.coa_id == "coa-1"
    assert len(coa.actions) == 1
    assert coa.mef_score == pytest.approx(0.72)


def test_game_state_construction():
    gs = GameState(
        state_id="gs-0",
        blue_assets=[],
        red_assets=[],
        turn=0,
    )
    assert gs.turn == 0
    assert gs.blue_assets == []


def test_mef_score_dataclass():
    score = MEFScore(coa_id="coa-1", effectiveness=0.9, cost=0.3, risk=0.2, composite=0.67)
    assert score.coa_id == "coa-1"
    assert score.composite == pytest.approx(0.67)


def test_compute_mef_score_default_weights():
    # 0.5*0.8 - 0.3*0.2 - 0.2*0.1 = 0.4 - 0.06 - 0.02 = 0.32
    result = compute_mef_score(effectiveness=0.8, cost=0.2, risk=0.1)
    assert result == pytest.approx(0.32)


def test_compute_mef_score_custom_weights():
    result = compute_mef_score(effectiveness=1.0, cost=0.0, risk=0.0, w_e=1.0, w_c=0.0, w_r=0.0)
    assert result == pytest.approx(1.0)


def test_self_play_engine_best_response_opposing_force():
    engine = SelfPlayEngine()
    gs = GameState(state_id="gs", blue_assets=[], red_assets=[], turn=0)
    blue_coa = CourseOfAction(coa_id="coa-b", force=Force.BLUE, actions=[], objective="hold")
    response = engine.best_response(blue_coa, gs)
    assert response.force == Force.RED


def test_self_play_engine_run_episode():
    engine = SelfPlayEngine()
    states = engine.run_episode(n_rounds=5)
    assert len(states) == 5
    assert all(isinstance(s, GameState) for s in states)
