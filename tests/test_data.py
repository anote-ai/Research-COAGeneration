"""Tests for coageneration data helpers."""

from __future__ import annotations

from coageneration.core import ActionCategory, Force
from coageneration.data import (
    make_action,
    make_asset,
    make_coa,
    make_coa_with_branch,
    make_cyber_ops_coa,
    make_game_state,
    make_info_ops_coa,
    make_logistics_coa,
)


def test_make_asset_defaults() -> None:
    asset = make_asset()
    assert asset.force == Force.BLUE
    assert 0.0 <= asset.capability_score <= 1.0


def test_make_action_with_tool() -> None:
    action = make_action(tool_name="nmap")
    assert action.tool_call is not None
    assert action.tool_call.tool_name == "nmap"


def test_make_action_no_tool() -> None:
    action = make_action()
    assert action.tool_call is None


def test_make_coa_actions_count() -> None:
    coa = make_coa(n_actions=5)
    assert len(coa.actions) == 5


def test_make_coa_domain_preserved() -> None:
    coa = make_coa(domain="cyber", seed=0)
    assert coa.domain == "cyber"


def test_cyber_ops_coa_domain() -> None:
    coa = make_cyber_ops_coa()
    assert coa.domain == "cyber"
    assert len(coa.actions) == 3


def test_logistics_coa_domain() -> None:
    coa = make_logistics_coa()
    assert coa.domain == "logistics"


def test_info_ops_coa_domain() -> None:
    coa = make_info_ops_coa()
    assert coa.domain == "information_ops"


def test_make_game_state_asset_counts() -> None:
    state = make_game_state(n_blue=4, n_red=3)
    assert len(state.blue_assets) == 4
    assert len(state.red_assets) == 3


def test_make_coa_with_branch_has_chain() -> None:
    coa = make_coa_with_branch()
    assert len(coa.chain) == 2
