"""Tests for envcage.env_ttl."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from envcage.env_ttl import (
    TTLEntry,
    expired_snapshots,
    get_ttl,
    list_ttl,
    remove_ttl,
    set_ttl,
)

_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def tf(tmp_path: Path) -> str:
    return str(tmp_path / "ttl.json")


# --- TTLEntry unit tests ---

def test_entry_not_expired_when_future():
    future = (_NOW + timedelta(hours=1)).isoformat()
    entry = TTLEntry(snapshot="snap.json", expires_at=future)
    assert not entry.is_expired(now=_NOW)


def test_entry_expired_when_past():
    past = (_NOW - timedelta(seconds=1)).isoformat()
    entry = TTLEntry(snapshot="snap.json", expires_at=past)
    assert entry.is_expired(now=_NOW)


def test_entry_seconds_remaining_positive():
    future = (_NOW + timedelta(seconds=90)).isoformat()
    entry = TTLEntry(snapshot="snap.json", expires_at=future)
    remaining = entry.seconds_remaining(now=_NOW)
    assert abs(remaining - 90.0) < 0.01


def test_entry_seconds_remaining_zero_when_expired():
    past = (_NOW - timedelta(seconds=10)).isoformat()
    entry = TTLEntry(snapshot="snap.json", expires_at=past)
    assert entry.seconds_remaining(now=_NOW) == 0.0


def test_to_dict_round_trips():
    future = (_NOW + timedelta(hours=1)).isoformat()
    entry = TTLEntry(snapshot="s.json", expires_at=future, note="test")
    assert TTLEntry.from_dict(entry.to_dict()) == entry


# --- set_ttl / get_ttl ---

def test_set_ttl_creates_file(tf):
    set_ttl("snap.json", seconds=3600, ttl_file=tf, now=_NOW)
    assert Path(tf).exists()


def test_set_ttl_file_is_valid_json(tf):
    set_ttl("snap.json", seconds=3600, ttl_file=tf, now=_NOW)
    data = json.loads(Path(tf).read_text())
    assert isinstance(data, dict)


def test_set_ttl_returns_entry(tf):
    entry = set_ttl("snap.json", seconds=60, ttl_file=tf, now=_NOW)
    assert entry.snapshot == "snap.json"
    assert not entry.is_expired(now=_NOW)


def test_get_ttl_returns_entry(tf):
    set_ttl("snap.json", seconds=60, ttl_file=tf, now=_NOW)
    entry = get_ttl("snap.json", ttl_file=tf)
    assert entry is not None
    assert entry.snapshot == "snap.json"


def test_get_ttl_returns_none_when_missing(tf):
    assert get_ttl("missing.json", ttl_file=tf) is None


def test_set_ttl_stores_note(tf):
    set_ttl("snap.json", seconds=60, note="refresh soon", ttl_file=tf, now=_NOW)
    entry = get_ttl("snap.json", ttl_file=tf)
    assert entry.note == "refresh soon"


# --- remove_ttl ---

def test_remove_ttl_deletes_entry(tf):
    set_ttl("snap.json", seconds=60, ttl_file=tf, now=_NOW)
    assert remove_ttl("snap.json", ttl_file=tf) is True
    assert get_ttl("snap.json", ttl_file=tf) is None


def test_remove_ttl_returns_false_when_missing(tf):
    assert remove_ttl("ghost.json", ttl_file=tf) is False


# --- list_ttl / expired_snapshots ---

def test_list_ttl_returns_all_entries(tf):
    set_ttl("a.json", seconds=60, ttl_file=tf, now=_NOW)
    set_ttl("b.json", seconds=120, ttl_file=tf, now=_NOW)
    entries = list_ttl(ttl_file=tf)
    assert len(entries) == 2
    assert {e.snapshot for e in entries} == {"a.json", "b.json"}


def test_expired_snapshots_filters_correctly(tf):
    past = _NOW - timedelta(hours=1)
    set_ttl("old.json", seconds=1, ttl_file=tf, now=past)   # already expired by _NOW
    set_ttl("new.json", seconds=7200, ttl_file=tf, now=_NOW)  # fresh
    expired = expired_snapshots(ttl_file=tf, now=_NOW)
    assert len(expired) == 1
    assert expired[0].snapshot == "old.json"


def test_list_ttl_empty_when_no_file(tf):
    assert list_ttl(ttl_file=tf) == []
