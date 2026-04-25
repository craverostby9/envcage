"""Tests for envcage.cli_type."""
import argparse
import json
import sys
from pathlib import Path

import pytest

from envcage.snapshot import save
from envcage.cli_type import cmd_type_show, cmd_type_check


@pytest.fixture
def snap_file(tmp_path):
    p = tmp_path / "snap.json"
    save(
        {
            "env": {
                "PORT": "9000",
                "DEBUG": "false",
                "API_URL": "https://api.test",
                "LABEL": "staging",
            }
        },
        str(p),
    )
    return str(p)


@pytest.fixture
def expected_file(tmp_path):
    p = tmp_path / "expected.json"
    p.write_text(json.dumps({"PORT": "int", "DEBUG": "bool", "API_URL": "url"}))
    return str(p)


@pytest.fixture
def mismatch_expected_file(tmp_path):
    p = tmp_path / "mismatch.json"
    p.write_text(json.dumps({"PORT": "string", "DEBUG": "int"}))
    return str(p)


def _args(**kwargs):
    ns = argparse.Namespace(json=False, **kwargs)
    return ns


# ---------------------------------------------------------------------------
# cmd_type_show
# ---------------------------------------------------------------------------

def test_cmd_type_show_prints_keys(snap_file, capsys):
    cmd_type_show(_args(snapshot=snap_file))
    out = capsys.readouterr().out
    assert "PORT" in out
    assert "int" in out


def test_cmd_type_show_prints_bool(snap_file, capsys):
    cmd_type_show(_args(snapshot=snap_file))
    out = capsys.readouterr().out
    assert "bool" in out


def test_cmd_type_show_json_output(snap_file, capsys):
    cmd_type_show(_args(snapshot=snap_file, json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    keys = [d["key"] for d in data]
    assert "PORT" in keys


def test_cmd_type_show_json_has_inferred_type(snap_file, capsys):
    cmd_type_show(_args(snapshot=snap_file, json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    port = next(d for d in data if d["key"] == "PORT")
    assert port["inferred_type"] == "int"


# ---------------------------------------------------------------------------
# cmd_type_check
# ---------------------------------------------------------------------------

def test_cmd_type_check_passes_when_types_match(snap_file, expected_file):
    with pytest.raises(SystemExit) as exc:
        cmd_type_check(_args(snapshot=snap_file, expected=expected_file))
    assert exc.value.code == 0


def test_cmd_type_check_fails_when_mismatch(snap_file, mismatch_expected_file):
    with pytest.raises(SystemExit) as exc:
        cmd_type_check(_args(snapshot=snap_file, expected=mismatch_expected_file))
    assert exc.value.code == 1


def test_cmd_type_check_prints_summary(snap_file, expected_file, capsys):
    with pytest.raises(SystemExit):
        cmd_type_check(_args(snapshot=snap_file, expected=expected_file))
    out = capsys.readouterr().out
    assert "match" in out.lower()


def test_cmd_type_check_json_output(snap_file, expected_file, capsys):
    with pytest.raises(SystemExit):
        cmd_type_check(_args(snapshot=snap_file, expected=expected_file, json=True))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "any_mismatches" in data
    assert data["any_mismatches"] is False


def test_cmd_type_check_missing_expected_file_exits_2(snap_file):
    with pytest.raises(SystemExit) as exc:
        cmd_type_check(_args(snapshot=snap_file, expected="/nonexistent/file.json"))
    assert exc.value.code == 2
