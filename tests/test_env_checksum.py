"""Tests for envcage.env_checksum."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envcage.env_checksum import (
    checksum,
    checksum_file,
    get_stored_checksum,
    record_checksum,
    verify_checksum,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def snap_file(tmp_path: Path) -> str:
    snap = {
        "env": {"APP_ENV": "production", "DB_HOST": "db.example.com"},
        "required": [],
    }
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(snap))
    return str(p)


@pytest.fixture()
def store_file(tmp_path: Path) -> str:
    return str(tmp_path / "checksums.json")


# ---------------------------------------------------------------------------
# checksum()
# ---------------------------------------------------------------------------

def test_checksum_returns_string():
    result = checksum({"A": "1"})
    assert isinstance(result, str)
    assert len(result) == 64  # sha256 hex digest


def test_checksum_identical_envs_match():
    env = {"X": "hello", "Y": "world"}
    assert checksum(env) == checksum(env)


def test_checksum_different_values_differ():
    assert checksum({"A": "1"}) != checksum({"A": "2"})


def test_checksum_key_order_does_not_matter():
    a = {"X": "1", "Y": "2"}
    b = {"Y": "2", "X": "1"}
    assert checksum(a) == checksum(b)


def test_checksum_empty_env():
    result = checksum({})
    assert isinstance(result, str)
    assert len(result) > 0


def test_checksum_algorithm_md5():
    result = checksum({"A": "1"}, algorithm="md5")
    assert len(result) == 32


def test_checksum_sha1_length():
    result = checksum({"A": "1"}, algorithm="sha1")
    assert len(result) == 40


# ---------------------------------------------------------------------------
# checksum_file()
# ---------------------------------------------------------------------------

def test_checksum_file_returns_string(snap_file: str):
    result = checksum_file(snap_file)
    assert isinstance(result, str)
    assert len(result) == 64


def test_checksum_file_stable(snap_file: str):
    assert checksum_file(snap_file) == checksum_file(snap_file)


def test_checksum_file_changes_after_edit(snap_file: str):
    before = checksum_file(snap_file)
    snap = json.loads(Path(snap_file).read_text())
    snap["env"]["NEW_KEY"] = "new_value"
    Path(snap_file).write_text(json.dumps(snap))
    after = checksum_file(snap_file)
    assert before != after


# ---------------------------------------------------------------------------
# record_checksum() / verify_checksum() / get_stored_checksum()
# ---------------------------------------------------------------------------

def test_record_checksum_creates_store(snap_file: str, store_file: str):
    record_checksum(snap_file, store_file)
    assert Path(store_file).exists()


def test_record_checksum_returns_digest(snap_file: str, store_file: str):
    digest = record_checksum(snap_file, store_file)
    assert len(digest) == 64


def test_record_checksum_persisted(snap_file: str, store_file: str):
    digest = record_checksum(snap_file, store_file)
    stored = get_stored_checksum(snap_file, store_file)
    assert stored == digest


def test_verify_checksum_passes_when_unchanged(snap_file: str, store_file: str):
    record_checksum(snap_file, store_file)
    assert verify_checksum(snap_file, store_file) is True


def test_verify_checksum_fails_when_changed(snap_file: str, store_file: str):
    record_checksum(snap_file, store_file)
    snap = json.loads(Path(snap_file).read_text())
    snap["env"]["TAMPERED"] = "yes"
    Path(snap_file).write_text(json.dumps(snap))
    assert verify_checksum(snap_file, store_file) is False


def test_verify_checksum_false_when_no_record(snap_file: str, store_file: str):
    assert verify_checksum(snap_file, store_file) is False


def test_get_stored_checksum_none_when_missing(snap_file: str, store_file: str):
    assert get_stored_checksum(snap_file, store_file) is None


def test_record_multiple_snapshots(tmp_path: Path, store_file: str):
    snaps = []
    for i in range(3):
        p = tmp_path / f"snap{i}.json"
        p.write_text(json.dumps({"env": {"KEY": str(i)}, "required": []}))
        snaps.append(str(p))
        record_checksum(str(p), store_file)

    store = json.loads(Path(store_file).read_text())
    assert len(store) == 3
