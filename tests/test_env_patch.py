"""Tests for envcage.env_patch."""
import json
import pytest
from pathlib import Path

from envcage.env_patch import (
    PatchOperation,
    apply_patch,
    patch_from_dict,
    load_patch_file,
    patch_snapshot_file,
)
from envcage.snapshot import save


@pytest.fixture
def base_env():
    return {"APP_NAME": "myapp", "DEBUG": "false", "PORT": "8080"}


def test_set_adds_new_key(base_env):
    ops = [PatchOperation(op="set", key="NEW_KEY", value="hello")]
    result = apply_patch(base_env, ops)
    assert result.patched["NEW_KEY"] == "hello"


def test_set_overwrites_existing_key(base_env):
    ops = [PatchOperation(op="set", key="DEBUG", value="true")]
    result = apply_patch(base_env, ops)
    assert result.patched["DEBUG"] == "true"


def test_delete_removes_key(base_env):
    ops = [PatchOperation(op="delete", key="PORT")]
    result = apply_patch(base_env, ops)
    assert "PORT" not in result.patched


def test_delete_missing_key_goes_to_skipped(base_env):
    ops = [PatchOperation(op="delete", key="NONEXISTENT")]
    result = apply_patch(base_env, ops)
    assert len(result.skipped) == 1
    assert result.skipped[0].key == "NONEXISTENT"


def test_unknown_op_goes_to_skipped(base_env):
    ops = [PatchOperation(op="rename", key="APP_NAME")]
    result = apply_patch(base_env, ops)
    assert len(result.skipped) == 1


def test_original_is_unchanged(base_env):
    ops = [PatchOperation(op="set", key="DEBUG", value="true")]
    result = apply_patch(base_env, ops)
    assert result.original["DEBUG"] == "false"


def test_applied_list_populated(base_env):
    ops = [
        PatchOperation(op="set", key="X", value="1"),
        PatchOperation(op="delete", key="PORT"),
    ]
    result = apply_patch(base_env, ops)
    assert len(result.applied) == 2


def test_patch_from_dict():
    raw = [{"op": "set", "key": "FOO", "value": "bar"}, {"op": "delete", "key": "BAZ"}]
    ops = patch_from_dict(raw)
    assert ops[0].op == "set"
    assert ops[1].value is None


def test_load_patch_file(tmp_path):
    pf = tmp_path / "patch.json"
    pf.write_text(json.dumps([{"op": "set", "key": "A", "value": "1"}]))
    ops = load_patch_file(str(pf))
    assert ops[0].key == "A"


def test_patch_snapshot_file(tmp_path):
    snap_path = str(tmp_path / "snap.json")
    patch_path = str(tmp_path / "patch.json")
    out_path = str(tmp_path / "out.json")

    snap = {"name": "test", "timestamp": "2024-01-01T00:00:00", "env": {"A": "1", "B": "2"}}
    save(snap, snap_path)
    Path(patch_path).write_text(json.dumps([{"op": "set", "key": "C", "value": "3"}, {"op": "delete", "key": "B"}]))

    result = patch_snapshot_file(snap_path, patch_path, out_path)
    assert "C" in result.patched
    assert "B" not in result.patched
    assert Path(out_path).exists()
