"""Tests for envcage.env_copy."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.env_copy import copy_snapshot, copy_snapshot_file, CopyResult
from envcage.snapshot import save


@pytest.fixture
def base_env():
    return {"APP_HOST": "localhost", "APP_PORT": "8080", "SECRET_KEY": "abc", "DEBUG": "true"}


def test_copy_snapshot_returns_all_keys_by_default(base_env):
    result_env, result = copy_snapshot(base_env)
    assert set(result_env) == set(base_env)


def test_copy_snapshot_returns_copy_result(base_env):
    _, result = copy_snapshot(base_env)
    assert isinstance(result, CopyResult)


def test_copy_snapshot_include_filters(base_env):
    result_env, result = copy_snapshot(base_env, include=["APP_HOST", "APP_PORT"])
    assert set(result_env) == {"APP_HOST", "APP_PORT"}
    assert "SECRET_KEY" in result.keys_skipped


def test_copy_snapshot_exclude_filters(base_env):
    result_env, result = copy_snapshot(base_env, exclude=["SECRET_KEY"])
    assert "SECRET_KEY" not in result_env
    assert "SECRET_KEY" in result.keys_skipped


def test_copy_snapshot_include_and_exclude_combined(base_env):
    result_env, result = copy_snapshot(
        base_env, include=["APP_HOST", "APP_PORT", "SECRET_KEY"], exclude=["SECRET_KEY"]
    )
    assert set(result_env) == {"APP_HOST", "APP_PORT"}


def test_copy_snapshot_preserves_values(base_env):
    result_env, _ = copy_snapshot(base_env)
    for k, v in base_env.items():
        assert result_env[k] == v


def test_copy_snapshot_is_deep_copy(base_env):
    result_env, _ = copy_snapshot(base_env)
    result_env["APP_HOST"] = "changed"
    assert base_env["APP_HOST"] == "localhost"


def test_copy_snapshot_total_copied(base_env):
    _, result = copy_snapshot(base_env, exclude=["DEBUG"])
    assert result.total_copied == 3


def test_copy_snapshot_empty_include_returns_nothing(base_env):
    result_env, result = copy_snapshot(base_env, include=[])
    assert result_env == {}
    assert len(result.keys_skipped) == len(base_env)


def test_copy_snapshot_file_creates_destination(tmp_path, base_env):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    snap = {"env": base_env, "required": []}
    save(snap, str(src))

    copy_snapshot_file(src, dst)
    assert dst.exists()


def test_copy_snapshot_file_destination_is_valid_json(tmp_path, base_env):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    save({"env": base_env, "required": []}, str(src))
    copy_snapshot_file(src, dst)
    data = json.loads(dst.read_text())
    assert "env" in data


def test_copy_snapshot_file_result_has_paths(tmp_path, base_env):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    save({"env": base_env, "required": []}, str(src))
    result = copy_snapshot_file(src, dst)
    assert str(src) in result.source
    assert str(dst) in result.destination


def test_copy_snapshot_file_exclude_persisted(tmp_path, base_env):
    src = tmp_path / "src.json"
    dst = tmp_path / "dst.json"
    save({"env": base_env, "required": []}, str(src))
    copy_snapshot_file(src, dst,_KEY"])
    data = json.loads(dst.read_text())
    assert "SECRET_KEY" not in data["env"]
