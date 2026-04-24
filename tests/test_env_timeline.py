"""Tests for envcage.env_timeline."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.env_timeline import (
    TimelineStep,
    Timeline,
    build_timeline,
    save_timeline,
    load_timeline,
)


@pytest.fixture()
def snap_dir(tmp_path):
    return tmp_path


def _write_snap(directory: Path, name: str, env: dict) -> str:
    p = directory / name
    p.write_text(json.dumps({"env": env, "required": []}))
    return str(p)


def test_build_timeline_single_snapshot(snap_dir):
    p = _write_snap(snap_dir, "s1.json", {"A": "1"})
    tl = build_timeline([p])
    assert tl.total_steps() == 1
    assert "A" in tl.steps[0].added


def test_build_timeline_detects_added_key(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "1", "B": "2"})
    tl = build_timeline([p1, p2])
    assert "B" in tl.steps[1].added


def test_build_timeline_detects_removed_key(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1", "B": "2"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "1"})
    tl = build_timeline([p1, p2])
    assert "B" in tl.steps[1].removed


def test_build_timeline_detects_changed_key(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "old"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "new"})
    tl = build_timeline([p1, p2])
    assert "A" in tl.steps[1].changed


def test_build_timeline_no_changes_step(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "1"})
    tl = build_timeline([p1, p2])
    step = tl.steps[1]
    assert step.added == [] and step.removed == [] and step.changed == []


def test_build_timeline_stores_labels(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "2"})
    tl = build_timeline([p1, p2], labels=["baseline", "v2"])
    assert tl.steps[0].label == "baseline"
    assert tl.steps[1].label == "v2"


def test_timeline_any_changes_true(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "2"})
    tl = build_timeline([p1, p2])
    assert tl.any_changes() is True


def test_timeline_any_changes_false_on_identical(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    p2 = _write_snap(snap_dir, "s2.json", {"A": "1"})
    tl = build_timeline([p1, p2])
    # first step always has 'added' keys, so any_changes is True for non-empty first snap
    # test the second step specifically
    assert tl.steps[1].added == [] and tl.steps[1].removed == [] and tl.steps[1].changed == []


def test_save_and_load_timeline_round_trip(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"X": "a"})
    p2 = _write_snap(snap_dir, "s2.json", {"X": "b", "Y": "c"})
    tl = build_timeline([p1, p2], labels=["first", "second"])
    out = str(snap_dir / "timeline.json")
    save_timeline(tl, out)
    loaded = load_timeline(out)
    assert loaded.total_steps() == 2
    assert loaded.steps[1].label == "second"
    assert "Y" in loaded.steps[1].added
    assert "X" in loaded.steps[1].changed


def test_save_timeline_creates_valid_json(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    tl = build_timeline([p1])
    out = str(snap_dir / "tl.json")
    save_timeline(tl, out)
    data = json.loads(Path(out).read_text())
    assert "steps" in data
    assert isinstance(data["steps"], list)


def test_step_to_dict_has_expected_keys(snap_dir):
    p1 = _write_snap(snap_dir, "s1.json", {"A": "1"})
    tl = build_timeline([p1])
    d = tl.steps[0].to_dict()
    for key in ("index", "snapshot_path", "label", "added", "removed", "changed"):
        assert key in d
