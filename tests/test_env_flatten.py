"""Tests for envcage.env_flatten."""
from __future__ import annotations

import json
import os

import pytest

from envcage.env_flatten import FlattenResult, flatten_env, flatten_snapshot_file


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
factory_env() -> dict:
    return {
        "APP_NAME": "myapp",
        "DATABASE": {"HOST": "localhost", "PORT": 5432},
        "FEATURES": ["auth", "billing"],
    }


@pytest.fixture()
def snap_file(tmp_path, factory_env):
    path = tmp_path / "snap.json"
    snap = {"env": factory_env, "timestamp": "2024-01-01T00:00:00"}
    path.write_text(json.dumps(snap))
    return str(path)


# ---------------------------------------------------------------------------
# flatten_env
# ---------------------------------------------------------------------------

def test_flatten_env_returns_flatten_result(factory_env):
    result = flatten_env(factory_env)
    assert isinstance(result, FlattenResult)


def test_flatten_env_scalar_key_preserved(factory_env):
    result = flatten_env(factory_env)
    assert "APP_NAME" in result.flattened
    assert result.flattened["APP_NAME"] == "myapp"


def test_flatten_env_nested_dict_expanded():
    env = {"DB": {"HOST": "localhost", "PORT": 5432}}
    result = flatten_env(env)
    assert "DB_HOST" in result.flattened
    assert "DB_PORT" in result.flattened
    assert result.flattened["DB_HOST"] == "localhost"
    assert result.flattened["DB_PORT"] == "5432"


def test_flatten_env_list_expanded():
    env = {"FEATURES": ["auth", "billing"]}
    result = flatten_env(env)
    assert "FEATURES_0" in result.flattened
    assert "FEATURES_1" in result.flattened
    assert result.flattened["FEATURES_0"] == "auth"


def test_flatten_env_none_value_becomes_empty_string():
    env = {"MISSING": None}
    result = flatten_env(env)
    assert result.flattened["MISSING"] == ""


def test_flatten_env_original_keys_recorded(factory_env):
    result = flatten_env(factory_env)
    assert set(result.original_keys) == set(factory_env.keys())


def test_flatten_env_produced_keys_match_flattened(factory_env):
    result = flatten_env(factory_env)
    assert set(result.produced_keys) == set(result.flattened.keys())


def test_flatten_env_total_produced_greater_than_original(factory_env):
    result = flatten_env(factory_env)
    assert result.total_produced > len(factory_env)


def test_flatten_env_custom_separator():
    env = {"DB": {"HOST": "h"}}
    result = flatten_env(env, sep=".")
    assert "DB.HOST" in result.flattened


def test_flatten_env_summary_string(factory_env):
    result = flatten_env(factory_env)
    s = result.summary()
    assert "Flattened" in s
    assert "env key" in s


# ---------------------------------------------------------------------------
# flatten_snapshot_file
# ---------------------------------------------------------------------------

def test_flatten_snapshot_file_creates_dest(tmp_path, snap_file):
    dest = str(tmp_path / "flat.json")
    flatten_snapshot_file(snap_file, dest)
    assert os.path.exists(dest)


def test_flatten_snapshot_file_dest_is_valid_json(tmp_path, snap_file):
    dest = str(tmp_path / "flat.json")
    flatten_snapshot_file(snap_file, dest)
    data = json.loads(open(dest).read())
    assert "env" in data


def test_flatten_snapshot_file_env_is_flat(tmp_path, snap_file):
    dest = str(tmp_path / "flat.json")
    flatten_snapshot_file(snap_file, dest)
    data = json.loads(open(dest).read())
    for v in data["env"].values():
        assert isinstance(v, str)


def test_flatten_snapshot_file_returns_flatten_result(tmp_path, snap_file):
    dest = str(tmp_path / "flat.json")
    result = flatten_snapshot_file(snap_file, dest)
    assert isinstance(result, FlattenResult)
