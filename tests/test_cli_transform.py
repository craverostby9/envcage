import json
import argparse
import pytest
from pathlib import Path
from envcage.cli_transform import cmd_transform, register


@pytest.fixture
def snap_file(tmp_path):
    f = tmp_path / "snap.json"
    f.write_text(json.dumps({"env": {"app_key": " hello ", "PORT": "80"}, "required": []}))
    return f


def _args(**kwargs):
    base = dict(uppercase=False, strip=False, replace_prefix=None)
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_cmd_transform_uppercase(snap_file, tmp_path, capsys):
    dest = str(tmp_path / "out.json")
    cmd_transform(_args(src=str(snap_file), dest=dest, uppercase=True))
    out = json.loads(Path(dest).read_text())
    assert "APP_KEY" in out["env"]


def test_cmd_transform_strip(snap_file, tmp_path, capsys):
    dest = str(tmp_path / "out.json")
    cmd_transform(_args(src=str(snap_file), dest=dest, strip=True))
    out = json.loads(Path(dest).read_text())
    assert out["env"]["app_key"] == "hello"


def test_cmd_transform_replace_prefix(tmp_path):
    src = tmp_path / "s.json"
    src.write_text(json.dumps({"env": {"OLD_HOST": "h", "OTHER": "x"}, "required": []}))
    dest = str(tmp_path / "out.json")
    cmd_transform(_args(src=str(src), dest=dest, replace_prefix="OLD_:NEW_"))
    out = json.loads(Path(dest).read_text())
    assert "NEW_HOST" in out["env"]


def test_cmd_transform_bad_replace_prefix_exits(snap_file, tmp_path):
    dest = str(tmp_path / "out.json")
    with pytest.raises(SystemExit):
        cmd_transform(_args(src=str(snap_file), dest=dest, replace_prefix="BADFORMAT"))


def test_cmd_transform_no_changes_message(snap_file, tmp_path, capsys):
    dest = str(tmp_path / "out.json")
    cmd_transform(_args(src=str(snap_file), dest=dest))
    captured = capsys.readouterr()
    assert "No changes" in captured.out


def test_register_adds_transform_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    register(sub)
    args = parser.parse_args(["transform", "src.json", "dest.json", "--uppercase"])
    assert args.uppercase is True
    assert args.src == "src.json"
