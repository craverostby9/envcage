"""Tests for envcage.cli_patch."""
import json
import argparse
import pytest
from pathlib import Path

from envcage.cli_patch import cmd_patch, cmd_patch_show
from envcage.snapshot import save


def _args(**kwargs):
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


@pytest.fixture
def snap_file(tmp_path):
    p = tmp_path / "snap.json"
    snap = {"name": "s", "timestamp": "2024-01-01T00:00:00", "env": {"A": "1", "B": "2"}}
    save(snap, str(p))
    return p


@pytest.fixture
def patch_file(tmp_path):
    p = tmp_path / "patch.json"
    p.write_text(json.dumps([{"op": "set", "key": "C", "value": "3"}, {"op": "delete", "key": "B"}]))
    return p


def test_cmd_patch_creates_output(tmp_path, snap_file, patch_file, capsys):
    out = tmp_path / "out.json"
    cmd_patch(_args(snapshot=str(snap_file), patch=str(patch_file), output=str(out)))
    assert out.exists()


def test_cmd_patch_prints_confirmation(tmp_path, snap_file, patch_file, capsys):
    out = tmp_path / "out.json"
    cmd_patch(_args(snapshot=str(snap_file), patch=str(patch_file), output=str(out)))
    captured = capsys.readouterr()
    assert "Applied" in captured.out


def test_cmd_patch_output_contains_new_key(tmp_path, snap_file, patch_file):
    out = tmp_path / "out.json"
    cmd_patch(_args(snapshot=str(snap_file), patch=str(patch_file), output=str(out)))
    data = json.loads(out.read_text())
    assert data["env"]["C"] == "3"


def test_cmd_patch_output_deleted_key_absent(tmp_path, snap_file, patch_file):
    out = tmp_path / "out.json"
    cmd_patch(_args(snapshot=str(snap_file), patch=str(patch_file), output=str(out)))
    data = json.loads(out.read_text())
    assert "B" not in data["env"]


def test_cmd_patch_missing_snapshot_exits(tmp_path, patch_file):
    out = tmp_path / "out.json"
    with pytest.raises(SystemExit):
        cmd_patch(_args(snapshot="/no/such/file.json", patch=str(patch_file), output=str(out)))


def test_cmd_patch_show_prints_ops(tmp_path, patch_file, capsys):
    cmd_patch_show(_args(patch=str(patch_file)))
    captured = capsys.readouterr()
    assert "SET" in captured.out
    assert "DELETE" in captured.out


def test_cmd_patch_show_empty_patch(tmp_path, capsys):
    pf = tmp_path / "empty.json"
    pf.write_text("[]")
    cmd_patch_show(_args(patch=str(pf)))
    captured = capsys.readouterr()
    assert "empty" in captured.out
