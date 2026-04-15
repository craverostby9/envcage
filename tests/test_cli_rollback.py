"""Tests for envcage.cli_rollback."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envcage.snapshot import save
from envcage.cli_rollback import cmd_rollback, cmd_rollback_log


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "source": "",
        "destination": "",
        "label": "rollback",
        "log_file": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def snap_file(tmp_path: Path) -> str:
    p = tmp_path / "snap.json"
    save({"DB_HOST": "localhost", "PORT": "5432"}, str(p))
    return str(p)


@pytest.fixture()
def dest_file(tmp_path: Path) -> str:
    return str(tmp_path / "current.json")


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    return str(tmp_path / "rb_log.json")


# --- cmd_rollback ---

def test_cmd_rollback_creates_destination(snap_file, dest_file, capsys):
    cmd_rollback(_args(source=snap_file, destination=dest_file))
    assert Path(dest_file).exists()


def test_cmd_rollback_prints_confirmation(snap_file, dest_file, capsys):
    cmd_rollback(_args(source=snap_file, destination=dest_file))
    out = capsys.readouterr().out
    assert "Rolled back" in out
    assert snap_file in out
    assert dest_file in out


def test_cmd_rollback_uses_label(snap_file, dest_file, capsys):
    cmd_rollback(_args(source=snap_file, destination=dest_file, label="v3"))
    out = capsys.readouterr().out
    assert "v3" in out


def test_cmd_rollback_writes_log(snap_file, dest_file, log_file):
    cmd_rollback(_args(source=snap_file, destination=dest_file, log_file=log_file))
    entries = json.loads(Path(log_file).read_text())
    assert len(entries) == 1


def test_cmd_rollback_missing_source_exits_one(dest_file):
    with pytest.raises(SystemExit) as exc_info:
        cmd_rollback(_args(source="/nonexistent/snap.json", destination=dest_file))
    assert exc_info.value.code == 1


# --- cmd_rollback_log ---

def test_cmd_rollback_log_empty(tmp_path, capsys):
    lf = str(tmp_path / "missing.json")
    cmd_rollback_log(_args(log_file=lf))
    out = capsys.readouterr().out
    assert "No rollback history" in out


def test_cmd_rollback_log_shows_entries(snap_file, dest_file, log_file, capsys):
    cmd_rollback(_args(source=snap_file, destination=dest_file, label="restore-1", log_file=log_file))
    cmd_rollback(_args(source=snap_file, destination=dest_file, label="restore-2", log_file=log_file))
    cmd_rollback_log(_args(log_file=log_file))
    out = capsys.readouterr().out
    assert "restore-1" in out
    assert "restore-2" in out
