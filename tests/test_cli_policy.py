"""Tests for envcage.cli_policy."""
import argparse
import json
import pytest
from pathlib import Path

from envcage.snapshot import capture, save
from envcage.policy import save_policy, create_policy
from envcage.cli_policy import cmd_policy_create, cmd_policy_show, cmd_policy_check


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        "output": None,
        "require": None,
        "forbid": None,
        "prefix": None,
        "max_empty": None,
        "description": "",
        "policy": None,
        "snapshot": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def snap_file(tmp_path):
    path = str(tmp_path / "snap.json")
    snap = capture(
        required_keys=["APP_NAME"],
        env={"APP_NAME": "myapp", "APP_ENV": "prod"},
    )
    save(snap, path)
    return path


@pytest.fixture
def policy_file(tmp_path):
    path = str(tmp_path / "policy.json")
    p = create_policy(required_keys=["APP_NAME"])
    save_policy(p, path)
    return path


def test_cmd_policy_create_writes_file(tmp_path):
    out = str(tmp_path / "policy.json")
    args = _args(output=out, require=["FOO", "BAR"])
    cmd_policy_create(args)
    assert Path(out).exists()


def test_cmd_policy_create_file_is_valid_json(tmp_path):
    out = str(tmp_path / "policy.json")
    args = _args(output=out, require=["FOO"])
    cmd_policy_create(args)
    data = json.loads(Path(out).read_text())
    assert "required_keys" in data


def test_cmd_policy_create_required_keys_persisted(tmp_path):
    out = str(tmp_path / "policy.json")
    args = _args(output=out, require=["DB_URL", "SECRET"])
    cmd_policy_create(args)
    data = json.loads(Path(out).read_text())
    assert "DB_URL" in data["required_keys"]
    assert "SECRET" in data["required_keys"]


def test_cmd_policy_create_forbidden_keys_persisted(tmp_path):
    out = str(tmp_path / "policy.json")
    args = _args(output=out, forbid=["DEBUG"])
    cmd_policy_create(args)
    data = json.loads(Path(out).read_text())
    assert "DEBUG" in data["forbidden_keys"]


def test_cmd_policy_create_max_empty_persisted(tmp_path):
    out = str(tmp_path / "policy.json")
    args = _args(output=out, max_empty=3)
    cmd_policy_create(args)
    data = json.loads(Path(out).read_text())
    assert data["max_empty_values"] == 3


def test_cmd_policy_show_prints_description(policy_file, capsys):
    args = _args(policy=policy_file)
    cmd_policy_show(args)
    out = capsys.readouterr().out
    assert "Description" in out


def test_cmd_policy_show_prints_required_keys(policy_file, capsys):
    args = _args(policy=policy_file)
    cmd_policy_show(args)
    out = capsys.readouterr().out
    assert "APP_NAME" in out


def test_cmd_policy_check_passes_exits_zero(snap_file, policy_file):
    args = _args(policy=policy_file, snapshot=snap_file)
    cmd_policy_check(args)  # should not raise SystemExit


def test_cmd_policy_check_fails_exits_one(tmp_path, snap_file):
    policy_path = str(tmp_path / "strict.json")
    p = create_policy(required_keys=["MISSING_KEY"])
    save_policy(p, policy_path)
    args = _args(policy=policy_path, snapshot=snap_file)
    with pytest.raises(SystemExit) as exc:
        cmd_policy_check(args)
    assert exc.value.code == 1


def test_cmd_policy_check_prints_summary(snap_file, policy_file, capsys):
    args = _args(policy=policy_file, snapshot=snap_file)
    cmd_policy_check(args)
    out = capsys.readouterr().out
    assert "passed" in out.lower()
