"""Tests for envcage.cli_snapshot_summary."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envcage.cli_snapshot_summary import cmd_summary, cmd_summary_single


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"json": False, "tags": "", "note": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def snap_file(tmp_path: Path) -> str:
    data = {
        "env": {
            "APP_KEY": "value1",
            "SECRET": "topsecret",
            "EMPTY": "",
        }
    }
    p = tmp_path / "mysnap.json"
    p.write_text(json.dumps(data))
    return str(p)


@pytest.fixture()
def snap_file2(tmp_path: Path) -> str:
    data = {"env": {"FOO": "bar"}}
    p = tmp_path / "other.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_cmd_summary_prints_output(snap_file, capsys):
    args = _args(snapshots=[snap_file])
    cmd_summary(args)
    out = capsys.readouterr().out
    assert "mysnap" in out


def test_cmd_summary_shows_key_count(snap_file, capsys):
    args = _args(snapshots=[snap_file])
    cmd_summary(args)
    out = capsys.readouterr().out
    assert "3" in out


def test_cmd_summary_json_output(snap_file, capsys):
    args = _args(snapshots=[snap_file], json=True)
    cmd_summary(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "entries" in data
    assert data["total_snapshots"] == 1


def test_cmd_summary_json_total_keys(snap_file, capsys):
    args = _args(snapshots=[snap_file], json=True)
    cmd_summary(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["total_keys"] == 3


def test_cmd_summary_multiple_snapshots(snap_file, snap_file2, capsys):
    args = _args(snapshots=[snap_file, snap_file2])
    cmd_summary(args)
    out = capsys.readouterr().out
    assert "mysnap" in out
    assert "other" in out


def test_cmd_summary_no_files_exits(capsys):
    args = _args(snapshots=[])
    with pytest.raises(SystemExit) as exc:
        cmd_summary(args)
    assert exc.value.code == 1


def test_cmd_summary_single_prints_name(snap_file, capsys):
    args = _args(snapshot=snap_file)
    cmd_summary_single(args)
    out = capsys.readouterr().out
    assert "mysnap" in out


def test_cmd_summary_single_shows_keys_label(snap_file, capsys):
    args = _args(snapshot=snap_file)
    cmd_summary_single(args)
    out = capsys.readouterr().out
    assert "Keys" in out


def test_cmd_summary_single_with_tags(snap_file, capsys):
    args = _args(snapshot=snap_file, tags="prod,v3")
    cmd_summary_single(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "v3" in out


def test_cmd_summary_single_with_note(snap_file, capsys):
    args = _args(snapshot=snap_file, note="initial baseline")
    cmd_summary_single(args)
    out = capsys.readouterr().out
    assert "initial baseline" in out
