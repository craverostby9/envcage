"""Tests for envcage.snapshot module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.snapshot import capture, list_snapshots, load, save


SAMPLE_ENV = {"APP_ENV": "production", "DEBUG": "false", "PORT": "8080"}


def test_capture_returns_required_keys():
    snap = capture(env=SAMPLE_ENV)
    assert "created_at" in snap
    assert "variables" in snap


def test_capture_stores_provided_env():
    snap = capture(env=SAMPLE_ENV)
    assert snap["variables"] == SAMPLE_ENV


def test_capture_uses_os_environ_by_default(monkeypatch):
    monkeypatch.setenv("ENVCAGE_TEST_VAR", "hello")
    snap = capture()
    assert snap["variables"]["ENVCAGE_TEST_VAR"] == "hello"


def test_save_creates_file(tmp_path):
    snap = capture(env=SAMPLE_ENV)
    file_path = save(snap, "staging", snapshot_dir=tmp_path)
    assert file_path.exists()
    assert file_path.name == "staging.json"


def test_save_file_is_valid_json(tmp_path):
    snap = capture(env=SAMPLE_ENV)
    file_path = save(snap, "staging", snapshot_dir=tmp_path)
    data = json.loads(file_path.read_text())
    assert data["variables"] == SAMPLE_ENV


def test_save_normalises_name(tmp_path):
    snap = capture(env=SAMPLE_ENV)
    file_path = save(snap, "My Snapshot", snapshot_dir=tmp_path)
    assert file_path.name == "my_snapshot.json"


def test_load_round_trip(tmp_path):
    snap = capture(env=SAMPLE_ENV)
    save(snap, "prod", snapshot_dir=tmp_path)
    loaded = load("prod", snapshot_dir=tmp_path)
    assert loaded["variables"] == SAMPLE_ENV


def test_load_raises_for_missing_snapshot(tmp_path):
    with pytest.raises(FileNotFoundError, match="missing"):
        load("missing", snapshot_dir=tmp_path)


def test_list_snapshots_empty(tmp_path):
    assert list_snapshots(snapshot_dir=tmp_path) == []


def test_list_snapshots_returns_names(tmp_path):
    for name in ("alpha", "beta", "gamma"):
        save(capture(env=SAMPLE_ENV), name, snapshot_dir=tmp_path)
    names = list_snapshots(snapshot_dir=tmp_path)
    assert names == ["alpha", "beta", "gamma"]


def test_list_snapshots_nonexistent_dir():
    assert list_snapshots(snapshot_dir=Path("/nonexistent/dir")) == []
