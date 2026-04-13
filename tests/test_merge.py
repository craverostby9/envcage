"""Tests for envcage.merge module."""

from __future__ import annotations

import json
import os
import tempfile

import pytest

from envcage.merge import MergeResult, merge_snapshot_files, merge_snapshots


@pytest.fixture
def snap_a():
    return {"env": {"HOST": "localhost", "PORT": "8080", "DEBUG": "true"}}


@pytest.fixture
def snap_b():
    return {"env": {"HOST": "prod.example.com", "PORT": "443", "LOG_LEVEL": "warn"}}


@pytest.fixture
def snap_c():
    return {"env": {"REGION": "us-east-1", "LOG_LEVEL": "error"}}


def test_merge_empty_list_returns_empty():
    result = merge_snapshots([])
    assert result.merged == {}
    assert not result.has_conflicts


def test_merge_single_snapshot(snap_a):
    result = merge_snapshots([snap_a])
    assert result.merged == snap_a["env"]
    assert not result.has_conflicts


def test_merge_last_wins_by_default(snap_a, snap_b):
    result = merge_snapshots([snap_a, snap_b])
    assert result.merged["HOST"] == "prod.example.com"
    assert result.merged["PORT"] == "443"


def test_merge_last_strategy_includes_all_keys(snap_a, snap_b):
    result = merge_snapshots([snap_a, snap_b])
    assert "DEBUG" in result.merged
    assert "LOG_LEVEL" in result.merged


def test_merge_first_strategy_keeps_first_value(snap_a, snap_b):
    result = merge_snapshots([snap_a, snap_b], strategy="first")
    assert result.merged["HOST"] == "localhost"
    assert result.merged["PORT"] == "8080"


def test_merge_first_strategy_includes_new_keys(snap_a, snap_b):
    result = merge_snapshots([snap_a, snap_b], strategy="first")
    assert "LOG_LEVEL" in result.merged


def test_merge_detects_conflicts(snap_a, snap_b):
    result = merge_snapshots([snap_a, snap_b])
    assert result.has_conflicts
    assert "HOST" in result.conflicts
    assert "PORT" in result.conflicts


def test_merge_no_conflicts_when_keys_disjoint():
    s1 = {"env": {"A": "1"}}
    s2 = {"env": {"B": "2"}}
    result = merge_snapshots([s1, s2])
    assert not result.has_conflicts
    assert result.merged == {"A": "1", "B": "2"}


def test_merge_conflict_tracks_all_values(snap_a, snap_b, snap_c):
    result = merge_snapshots([snap_a, snap_b, snap_c])
    assert "LOG_LEVEL" in result.conflicts
    assert set(result.conflicts["LOG_LEVEL"]) == {"warn", "error"}


def test_merge_sources_stored_in_result(snap_a, snap_b):
    result = merge_snapshots([snap_a, snap_b], sources=["a.json", "b.json"])
    assert result.sources == ["a.json", "b.json"]


def test_merge_snapshot_files_loads_and_merges():
    snap1 = {"env": {"KEY": "value1", "ONLY_IN_1": "yes"}}
    snap2 = {"env": {"KEY": "value2", "ONLY_IN_2": "yes"}}

    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = os.path.join(tmpdir, "snap1.json")
        path2 = os.path.join(tmpdir, "snap2.json")

        with open(path1, "w") as f:
            json.dump(snap1, f)
        with open(path2, "w") as f:
            json.dump(snap2, f)

        result = merge_snapshot_files([path1, path2])

    assert result.merged["KEY"] == "value2"
    assert "ONLY_IN_1" in result.merged
    assert "ONLY_IN_2" in result.merged


def test_merge_snapshot_files_saves_output():
    snap1 = {"env": {"A": "1"}}
    snap2 = {"env": {"B": "2"}}

    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = os.path.join(tmpdir, "snap1.json")
        path2 = os.path.join(tmpdir, "snap2.json")
        out_path = os.path.join(tmpdir, "merged.json")

        with open(path1, "w") as f:
            json.dump(snap1, f)
        with open(path2, "w") as f:
            json.dump(snap2, f)

        merge_snapshot_files([path1, path2], output_path=out_path)

        assert os.path.exists(out_path)
        with open(out_path) as f:
            saved = json.load(f)
        assert saved["env"]["A"] == "1"
        assert saved["env"]["B"] == "2"
