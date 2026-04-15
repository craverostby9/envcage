"""Tests for envcage.env_lock."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.env_lock import (
    LockEntry,
    get_lock,
    is_locked,
    list_locks,
    lock_snapshot,
    unlock_snapshot,
)


@pytest.fixture()
def lf(tmp_path) -> str:
    return str(tmp_path / "locks.json")


def test_lock_snapshot_creates_entry(lf):
    entry = lock_snapshot("snap_a.json", lock_file=lf)
    assert entry.snapshot == "snap_a.json"


def test_lock_snapshot_persists_to_file(lf):
    lock_snapshot("snap_a.json", lock_file=lf)
    data = json.loads(Path(lf).read_text())
    assert "snap_a.json" in data


def test_lock_snapshot_stores_reason(lf):
    lock_snapshot("snap_a.json", reason="production freeze", lock_file=lf)
    entry = get_lock("snap_a.json", lock_file=lf)
    assert entry is not None
    assert entry.reason == "production freeze"


def test_lock_snapshot_stores_timestamp(lf):
    entry = lock_snapshot("snap_a.json", lock_file=lf)
    assert "T" in entry.locked_at  # ISO-8601 format


def test_is_locked_returns_true_after_lock(lf):
    lock_snapshot("snap_a.json", lock_file=lf)
    assert is_locked("snap_a.json", lock_file=lf) is True


def test_is_locked_returns_false_when_not_locked(lf):
    assert is_locked("snap_b.json", lock_file=lf) is False


def test_unlock_snapshot_removes_lock(lf):
    lock_snapshot("snap_a.json", lock_file=lf)
    unlock_snapshot("snap_a.json", lock_file=lf)
    assert is_locked("snap_a.json", lock_file=lf) is False


def test_unlock_snapshot_returns_true_when_was_locked(lf):
    lock_snapshot("snap_a.json", lock_file=lf)
    assert unlock_snapshot("snap_a.json", lock_file=lf) is True


def test_unlock_snapshot_returns_false_when_not_locked(lf):
    assert unlock_snapshot("snap_x.json", lock_file=lf) is False


def test_get_lock_returns_none_when_missing(lf):
    assert get_lock("missing.json", lock_file=lf) is None


def test_get_lock_returns_entry(lf):
    lock_snapshot("snap_a.json", reason="ci", lock_file=lf)
    entry = get_lock("snap_a.json", lock_file=lf)
    assert isinstance(entry, LockEntry)
    assert entry.reason == "ci"


def test_list_locks_returns_all(lf):
    lock_snapshot("snap_a.json", lock_file=lf)
    lock_snapshot("snap_b.json", lock_file=lf)
    locks = list_locks(lock_file=lf)
    names = {e.snapshot for e in locks}
    assert names == {"snap_a.json", "snap_b.json"}


def test_list_locks_empty_when_no_file(lf):
    assert list_locks(lock_file=lf) == []


def test_lock_overwrite_updates_timestamp(lf):
    e1 = lock_snapshot("snap_a.json", lock_file=lf)
    e2 = lock_snapshot("snap_a.json", reason="updated", lock_file=lf)
    assert e2.reason == "updated"
    assert len(list_locks(lock_file=lf)) == 1
