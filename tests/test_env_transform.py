import json
import pytest
from pathlib import Path
from envcage.env_transform import (
    uppercase_keys, strip_values, replace_prefix,
    apply_transforms, transform_snapshot_file,
)


@pytest.fixture
def sample_env():
    return {"db_host": "localhost", "db_port": " 5432 ", "APP_NAME": "envcage"}


def test_uppercase_keys_converts_all(sample_env):
    result = uppercase_keys(sample_env)
    assert all(k == k.upper() for k in result.transformed)


def test_uppercase_keys_preserves_values(sample_env):
    result = uppercase_keys(sample_env)
    assert result.transformed["APP_NAME"] == "envcage"


def test_uppercase_keys_records_changes(sample_env):
    result = uppercase_keys(sample_env)
    assert "db_host" in result.changes
    assert "APP_NAME" not in result.changes


def test_strip_values_removes_whitespace():
    env = {"KEY": "  value  ", "CLEAN": "ok"}
    result = strip_values(env)
    assert result.transformed["KEY"] == "value"
    assert result.transformed["CLEAN"] == "ok"


def test_strip_values_records_only_dirty_keys():
    env = {"KEY": "  value  ", "CLEAN": "ok"}
    result = strip_values(env)
    assert "KEY" in result.changes
    assert "CLEAN" not in result.changes


def test_replace_prefix_renames_matching_keys():
    env = {"OLD_HOST": "localhost", "OLD_PORT": "5432", "OTHER": "x"}
    result = replace_prefix(env, "OLD_", "NEW_")
    assert "NEW_HOST" in result.transformed
    assert "NEW_PORT" in result.transformed
    assert "OLD_HOST" not in result.transformed
    assert "OTHER" in result.transformed


def test_replace_prefix_records_changed_keys():
    env = {"OLD_HOST": "localhost", "OTHER": "x"}
    result = replace_prefix(env, "OLD_", "NEW_")
    assert "OLD_HOST" in result.changes
    assert "OTHER" not in result.changes


def test_apply_transforms_uppercase_and_strip():
    env = {"key": "  val  "}
    result = apply_transforms(env, uppercase=True, strip=True)
    assert "KEY" in result.transformed
    assert result.transformed["KEY"] == "val"


def test_apply_transforms_no_flags_returns_copy():
    env = {"KEY": "val"}
    result = apply_transforms(env)
    assert result.transformed == env
    assert result.changes == []


def test_transform_snapshot_file(tmp_path):
    src = tmp_path / "snap.json"
    dest = tmp_path / "out.json"
    snap = {"env": {"app_host": " localhost ", "PORT": "8080"}, "required": []}
    src.write_text(json.dumps(snap))
    result = transform_snapshot_file(str(src), str(dest), uppercase=True, strip=True)
    out = json.loads(dest.read_text())
    assert out["env"]["APP_HOST"] == "localhost"
    assert out["env"]["PORT"] == "8080"
    assert "app_host" in result.changes
