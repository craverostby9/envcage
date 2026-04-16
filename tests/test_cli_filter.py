"""Tests for envcage.cli_filter."""
from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from envcage.cli_filter import cmd_filter
from envcage.snapshot import save


@pytest.fixture()
def snap_file(tmp_path):
    env = {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "secret",
        "DB_HOST": "localhost",
        "EMPTY_VAR": "",
    }
    p = tmp_path / "snap.json"
    save({"env": env}, str(p))
    return str(p)


def _args(**kwargs):
    defaults = dict(
        pattern="",
        prefix=None,
        sensitive=False,
        non_sensitive=False,
        empty=False,
        case_sensitive=False,
        keys_only=False,
    )
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def test_cmd_filter_no_options_prints_all(snap_file, capsys):
    cmd_filter(_args(snapshot=snap_file))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "APP_NAME" in data
    assert "DB_HOST" in data


def test_cmd_filter_pattern(snap_file, capsys):
    cmd_filter(_args(snapshot=snap_file, pattern=r"^DB_"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert set(data.keys()) == {"DB_PASSWORD", "DB_HOST"}


def test_cmd_filter_prefix(snap_file, capsys):
    cmd_filter(_args(snapshot=snap_file, prefix=["APP_"]))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert list(data.keys()) == ["APP_NAME"]


def test_cmd_filter_sensitive(snap_file, capsys):
    cmd_filter(_args(snapshot=snap_file, sensitive=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "DB_PASSWORD" in data
    assert "APP_NAME" not in data


def test_cmd_filter_empty(snap_file, capsys):
    cmd_filter(_args(snapshot=snap_file, empty=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data == {"EMPTY_VAR": ""}


def test_cmd_filter_keys_only(snap_file, capsys):
    cmd_filter(_args(snapshot=snap_file, pattern=r"^DB_", keys_only=True))
    out = capsys.readouterr().out.strip().splitlines()
    assert sorted(out) == ["DB_HOST", "DB_PASSWORD"]


def test_cmd_filter_missing_file_exits(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cmd_filter(_args(snapshot=str(tmp_path / "missing.json")))
    assert exc.value.code == 1
