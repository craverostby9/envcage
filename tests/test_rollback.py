"""Tests for envcage.rollback."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.snapshot import save
from envcage.rollback import rollback, rollback_log, RollbackRecord, to_dict, from_dict


@pytest.fixture()
def snap_file(tmp_path: Path) -> str:
    p = tmp_path / "snap.json"
    save({"APP_ENV": "staging", "PORT": "8080"}, str(p))
    return str(p)


@pytest.fixture()
def dest_file(tmp_path: Path) -> str:
    return str(tmp_path / "current.json")


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    return str(tmp_path / "rollback_log.json")


# --- RollbackRecord helpers ---

def test_to_dict_round_trips():
    r = RollbackRecord(label="v1", source="a.json", destination="b.json", env={"X": "1"})
    assert from_dict(to_dict(r)).label == "v1"
    assert from_dict(to_dict(r)).env == {"X": "1"}


# --- rollback() ---

def test_rollback_creates_destination(snap_file, dest_file):
    rollback(snap_file, dest_file)
    assert Path(dest_file).exists()


def test_rollback_destination_contains_source_env(snap_file, dest_file):
    rollback(snap_file, dest_file)
    data = json.loads(Path(dest_file).read_text())
    assert data["env"]["APP_ENV"] == "staging"


def test_rollback_returns_record(snap_file, dest_file):
    rec = rollback(snap_file, dest_file, label="restore-v2")
    assert isinstance(rec, RollbackRecord)
    assert rec.label == "restore-v2"
    assert rec.source == snap_file
    assert rec.destination == dest_file


def test_rollback_record_env_matches_source(snap_file, dest_file):
    rec = rollback(snap_file, dest_file)
    assert rec.env["PORT"] == "8080"


def test_rollback_writes_log(snap_file, dest_file, log_file):
    rollback(snap_file, dest_file, log_file=log_file)
    assert Path(log_file).exists()
    entries = json.loads(Path(log_file).read_text())
    assert len(entries) == 1
    assert entries[0]["label"] == "rollback"


def test_rollback_appends_to_existing_log(snap_file, dest_file, log_file):
    rollback(snap_file, dest_file, label="first", log_file=log_file)
    rollback(snap_file, dest_file, label="second", log_file=log_file)
    entries = json.loads(Path(log_file).read_text())
    assert len(entries) == 2
    assert entries[1]["label"] == "second"


# --- rollback_log() ---

def test_rollback_log_returns_empty_when_no_file(tmp_path):
    result = rollback_log(str(tmp_path / "missing.json"))
    assert result == []


def test_rollback_log_returns_records(snap_file, dest_file, log_file):
    rollback(snap_file, dest_file, label="alpha", log_file=log_file)
    records = rollback_log(log_file)
    assert len(records) == 1
    assert isinstance(records[0], RollbackRecord)
    assert records[0].label == "alpha"
