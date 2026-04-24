"""Tests for envcage.env_interpolate."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from envcage.env_interpolate import (
    interpolate_snapshot,
    interpolate_snapshot_file,
    InterpolateResult,
    _refs_in,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_env():
    return {
        "HOME": "/home/user",
        "CONFIG_DIR": "${HOME}/.config",
        "CACHE_DIR": "$HOME/.cache",
        "PLAIN": "no-refs-here",
        "BROKEN": "${MISSING_VAR}/data",
    }


# ---------------------------------------------------------------------------
# _refs_in
# ---------------------------------------------------------------------------

def test_refs_in_brace_style():
    assert _refs_in("${FOO}/bar") == ["FOO"]


def test_refs_in_dollar_style():
    assert _refs_in("$FOO/bar") == ["FOO"]


def test_refs_in_multiple():
    refs = _refs_in("${A}:${B}:$C")
    assert refs == ["A", "B", "C"]


def test_refs_in_no_refs():
    assert _refs_in("plain-value") == []


# ---------------------------------------------------------------------------
# interpolate_snapshot
# ---------------------------------------------------------------------------

def test_interpolate_resolves_brace_reference(base_env):
    result = interpolate_snapshot(base_env)
    assert result.env["CONFIG_DIR"] == "/home/user/.config"


def test_interpolate_resolves_dollar_reference(base_env):
    result = interpolate_snapshot(base_env)
    assert result.env["CACHE_DIR"] == "/home/user/.cache"


def test_interpolate_plain_value_unchanged(base_env):
    result = interpolate_snapshot(base_env)
    assert result.env["PLAIN"] == "no-refs-here"


def test_interpolate_resolved_keys_listed(base_env):
    result = interpolate_snapshot(base_env)
    assert "CONFIG_DIR" in result.resolved
    assert "CACHE_DIR" in result.resolved


def test_interpolate_unresolved_keys_listed(base_env):
    result = interpolate_snapshot(base_env)
    assert "BROKEN" in result.unresolved


def test_interpolate_unresolved_value_left_intact(base_env):
    result = interpolate_snapshot(base_env)
    assert result.env["BROKEN"] == "${MISSING_VAR}/data"


def test_interpolate_any_unresolved_flag(base_env):
    result = interpolate_snapshot(base_env)
    assert result.any_unresolved is True


def test_interpolate_no_unresolved_flag():
    env = {"A": "hello", "B": "${A} world"}
    result = interpolate_snapshot(env)
    assert result.any_unresolved is False


def test_interpolate_strict_raises_on_missing(base_env):
    with pytest.raises(KeyError, match="MISSING_VAR"):
        interpolate_snapshot(base_env, strict=True)


def test_interpolate_external_context_used():
    env = {"MSG": "Hello ${NAME}"}
    result = interpolate_snapshot(env, context={"NAME": "World"})
    assert result.env["MSG"] == "Hello World"
    assert "MSG" in result.resolved


def test_interpolate_returns_interpolate_result(base_env):
    result = interpolate_snapshot(base_env)
    assert isinstance(result, InterpolateResult)


# ---------------------------------------------------------------------------
# interpolate_snapshot_file
# ---------------------------------------------------------------------------

def test_interpolate_snapshot_file_creates_dest(tmp_path):
    from envcage.snapshot import save
    src = tmp_path / "src.json"
    dest = tmp_path / "dest.json"
    snap = {"env": {"BASE": "/opt", "FULL": "${BASE}/app"}, "required": []}
    save(snap, str(src))
    interpolate_snapshot_file(src, dest)
    assert dest.exists()


def test_interpolate_snapshot_file_resolves_values(tmp_path):
    from envcage.snapshot import save, load
    src = tmp_path / "src.json"
    dest = tmp_path / "dest.json"
    snap = {"env": {"BASE": "/opt", "FULL": "${BASE}/app"}, "required": []}
    save(snap, str(src))
    interpolate_snapshot_file(src, dest)
    loaded = load(str(dest))
    assert loaded["env"]["FULL"] == "/opt/app"
