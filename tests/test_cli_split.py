"""Tests for envcage.cli_split."""
import argparse
import pytest
from envcage.cli_split import cmd_split, register
from envcage.snapshot import save


@pytest.fixture
def snap_file(tmp_path):
    p = tmp_path / "snap.json"
    save({"env": {"APP_HOST": "localhost", "DB_HOST": "db", "LOG": "info"}, "required": []}, str(p))
    return str(p)


def _args(**kwargs):
    base = dict(source=None, prefix=None, group=None, output_dir=".", strip_prefix=False)
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_cmd_split_by_prefix_creates_files(snap_file, tmp_path):
    args = _args(source=snap_file, prefix=["APP_", "DB_"], output_dir=str(tmp_path))
    cmd_split(args)
    assert (tmp_path / "APP.json").exists()
    assert (tmp_path / "DB.json").exists()


def test_cmd_split_prints_summary(snap_file, tmp_path, capsys):
    args = _args(source=snap_file, prefix=["APP_"], output_dir=str(tmp_path))
    cmd_split(args)
    out = capsys.readouterr().out
    assert "Split into" in out


def test_cmd_split_no_options_exits(snap_file, tmp_path):
    args = _args(source=snap_file, output_dir=str(tmp_path))
    with pytest.raises(SystemExit) as exc:
        cmd_split(args)
    assert exc.value.code == 1


def test_cmd_split_by_group(snap_file, tmp_path):
    args = _args(source=snap_file, group=["web:APP_HOST", "db:DB_HOST"], output_dir=str(tmp_path))
    cmd_split(args)
    assert (tmp_path / "web.json").exists()
    assert (tmp_path / "db.json").exists()


def test_cmd_split_invalid_group_exits(snap_file, tmp_path):
    args = _args(source=snap_file, group=["badspec"], output_dir=str(tmp_path))
    with pytest.raises(SystemExit) as exc:
        cmd_split(args)
    assert exc.value.code == 1


def test_register_adds_split_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register(sub)
    parsed = parser.parse_args(["split", "snap.json", "--prefix", "APP_"])
    assert parsed.prefix == ["APP_"]
