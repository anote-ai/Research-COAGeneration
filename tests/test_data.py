"""Tests for coageneration.data."""

import pytest
from coageneration.core import Action, Asset, CourseOfAction, Force, GameState
from coageneration.data import make_action, make_asset, make_coa, make_game_state


def test_make_asset_returns_asset():
    a = make_asset(force=Force.RED, capability=0.6)
    assert isinstance(a, Asset)
    assert a.force == Force.RED
    assert a.capability_score == pytest.approx(0.6)


def test_make_action_returns_action():
    a = make_action(asset_id="x1", action_type="recon")
    assert isinstance(a, Action)
    assert a.action_type == "recon"


def test_make_coa_returns_coa():
    coa = make_coa(force=Force.BLUE, n_actions=4, seed=1)
    assert isinstance(coa, CourseOfAction)
    assert len(coa.actions) == 4
    assert coa.force == Force.BLUE


def test_make_game_state_asset_counts():
    state = make_game_state(n_blue=3, n_red=4, seed=7)
    assert isinstance(state, GameState)
    assert len(state.blue_assets) == 3
    assert len(state.red_assets) == 4
