"""Tests for LLMPolicy and the pluggable-policy SelfPlayEngine."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from coageneration.core import (
    Action,
    ActionCategory,
    CourseOfAction,
    Force,
    GameState,
    Policy,
    SelfPlayEngine,
)
from coageneration.data import make_coa, make_game_state
from coageneration.llm_policy import LLMPolicy, _parse_llm_response


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_RESPONSE = {
    "objective": "suppress enemy advance",
    "actions": [
        {
            "action_type": "defend",
            "category": "kinetic",
            "asset_id": "red-000",
            "priority": 7,
            "target_location": [45.0, 55.0],
            "expected_duration_s": 120.0,
        },
        {
            "action_type": "jam",
            "category": "cyber",
            "asset_id": "red-001",
            "priority": 3,
            "target_location": [40.0, 60.0],
            "expected_duration_s": 60.0,
        },
    ],
    "mef_components": {"effectiveness": 0.7, "cost": 0.25, "risk": 0.15},
}


def _make_mock_client(response_json: dict) -> MagicMock:
    """Return a mock Anthropic client that returns response_json as text."""
    content_block = SimpleNamespace(text=json.dumps(response_json))
    message = SimpleNamespace(content=[content_block])
    client = MagicMock()
    client.messages.create.return_value = message
    return client


# ---------------------------------------------------------------------------
# _parse_llm_response
# ---------------------------------------------------------------------------


def test_parse_valid_response() -> None:
    state = make_game_state(n_blue=2, n_red=2, seed=0)
    raw = json.dumps(_VALID_RESPONSE)
    coa = _parse_llm_response(raw, Force.RED, state)
    assert coa.force == Force.RED
    assert len(coa.actions) == 2
    assert coa.objective == "suppress enemy advance"
    assert -1.0 <= coa.mef_score <= 1.0


def test_parse_invalid_json_returns_fallback() -> None:
    state = make_game_state(n_blue=2, n_red=2, seed=0)
    coa = _parse_llm_response("not valid json {{{", Force.RED, state)
    assert coa.force == Force.RED
    assert len(coa.actions) >= 1


def test_parse_unknown_asset_id_replaced() -> None:
    state = make_game_state(n_blue=2, n_red=2, seed=0)
    bad = dict(_VALID_RESPONSE)
    bad["actions"] = [
        {
            "action_type": "attack",
            "category": "kinetic",
            "asset_id": "nonexistent-999",
            "priority": 5,
            "target_location": [10.0, 20.0],
            "expected_duration_s": 30.0,
        }
    ]
    coa = _parse_llm_response(json.dumps(bad), Force.RED, state)
    valid_ids = {a.asset_id for a in state.red_assets}
    assert all(a.asset_id in valid_ids for a in coa.actions)


def test_parse_strips_markdown_fences() -> None:
    state = make_game_state(n_red=2, seed=0)
    wrapped = "```json\n" + json.dumps(_VALID_RESPONSE) + "\n```"
    coa = _parse_llm_response(wrapped, Force.RED, state)
    assert len(coa.actions) == 2


# ---------------------------------------------------------------------------
# LLMPolicy.generate_coa
# ---------------------------------------------------------------------------


def test_llm_policy_generate_coa_calls_client() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=1)
    blue_coa = make_coa(force=Force.BLUE, n_actions=2, seed=1)
    client = _make_mock_client(_VALID_RESPONSE)

    policy = LLMPolicy(client=client, model="claude-sonnet-4-6")
    coa = policy.generate_coa(state, blue_coa)

    client.messages.create.assert_called_once()
    assert coa.force == Force.RED
    assert len(coa.actions) >= 1


def test_llm_policy_responding_force_override() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=2)
    red_coa = make_coa(force=Force.RED, n_actions=2, seed=2)
    client = _make_mock_client(_VALID_RESPONSE)

    policy = LLMPolicy(client=client)
    coa = policy.generate_coa(state, red_coa, responding_force=Force.BLUE)
    assert coa.force == Force.BLUE


def test_llm_policy_chain_built() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=3)
    blue_coa = make_coa(force=Force.BLUE, n_actions=2, seed=3)
    client = _make_mock_client(_VALID_RESPONSE)

    policy = LLMPolicy(client=client)
    coa = policy.generate_coa(state, blue_coa)
    assert len(coa.chain) == len(coa.actions)


# ---------------------------------------------------------------------------
# SelfPlayEngine with pluggable policy
# ---------------------------------------------------------------------------


def test_engine_uses_policy_when_provided() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=4)
    client = _make_mock_client(_VALID_RESPONSE)
    policy = LLMPolicy(client=client)

    engine = SelfPlayEngine(seed=4, policy=policy)
    states = engine.run_episode(state, n_rounds=2)

    assert len(states) == 3
    assert client.messages.create.call_count == 2  # one call per round


def test_engine_without_policy_uses_random() -> None:
    state = make_game_state(n_blue=3, n_red=3, seed=5)
    engine = SelfPlayEngine(seed=5)
    states = engine.run_episode(state, n_rounds=3)
    assert len(states) == 4


def test_policy_abstract_interface_raises() -> None:
    policy = Policy()
    with pytest.raises(NotImplementedError):
        policy.generate_coa(make_game_state(), make_coa())
