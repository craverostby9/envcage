"""Tests for envcage.cli_timeline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envcage.cli_timeline import cmd_timeline_build, cmd_timeline_show


def _args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def _write_snap(directory: Path, name: str, env: dict) -> str:
    p = directory / name
    p.write_text(json.dumps({"env": env, "required": []}))
    return str(p)


@pytest.fixture()
def snap_dir(tmp_path):
    return tmp_path


def test_cmd_timeline_build_prints_steps(snap_dir, capsys):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "2", "B": "3"})
    cmd_timeline_build(_args(snapshots=[p1, p2], labels=None, output=None))
    out = capsys.readouterr().out
    assert "Step 0" in out
    assert "Step 1" in out


def test_cmd_timeline_build_shows_added_key(snap_dir, capsys):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "1", "NEW": "x"})
    cmd_timeline_build(_args(snapshots=[p1, p2], labels=None, output=None))
    out = capsys.readouterr().out
    assert "NEW" in out


def test_cmd_timeline_build_saves_file(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "2"})
    out_file = str(snap_dir / "tl.json")
    cmd_timeline_build(_args(snapshots=[p1, p2], labels=None, output=out_file))
    assert Path(out_file).exists()


def test_cmd_timeline_build_saved_file_is_valid_json(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    out_file = str(snap_dir / "tl.json")
    cmd_timeline_build(_args(snapshots=[p1], labels=None, output=out_file))
    data = json.loads(Path(out_file).read_text())
    assert "steps" in data


def test_cmd_timeline_build_label_mismatch_exits(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "2"})
    with pytest.raises(SystemExit):
        cmd_timeline_build(
            _args(snapshots=[p1, p2], labels="only-one-label", output=None)
        )


def test_cmd_timeline_build_prints_confirmation_when_saved(snap_dir, capsys):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    out_file = str(snap_dir / "tl.json")
    cmd_timeline_build(_args(snapshots=[p1], labels=None, output=out_file))
    out = capsys.readouterr().out
    assert "saved" in out.lower() or "timeline" in out.lower()


def test_cmd_timeline_show_prints_summary(snap_dir, capsys):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "2"})
    tl_file = str(snap_dir / "tl.json")
    cmd_timeline_build(_args(snapshots=[p1, p2], labels=None, output=tl_file))
    capsys.readouterr()  # clear
    cmd_timeline_show(_args(timeline_file=tl_file))
    out = capsys.readouterr().out
    assert "Timeline" in out
    assert "2 step" in out


def test_cmd_timeline_show_lists_each_step(snap_dir, capsys):
    p1 = _write_snap(snap_dir, "s1.json", {"X": "a"})
    p2 = _write_snap(snap_dir, "s2.json", {"X": "b"})
    p3 = _write_snap(snap_dir, "s3.json", {"X": "c", "Y": "d"})
    tl_file = str(snap_dir / "tl.json")
    cmd_timeline_build(_args(snapshots=[p1, p2, p3], labels=None, output=tl_file))
    capsys.readouterr()
    cmd_timeline_show(_args(timeline_file=tl_file))
    out = capsys.readouterr().out
    assert "[0]" in out
    assert "[1]" in out
    assert "[2]" in out
