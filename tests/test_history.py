"""Tests for envcage.history."""

import json
import pytest
from pathlib import Path

from envcage.history import (
    record_snapshot,
    load_history,
    find_by_tag,
    find_by_name,
    clear_history,
    HistoryEntry,
)


@pytest.fixture
def history_file(tmp_path):
    return str(tmp_path / "test_history.json")


def test_record_snapshot_creates_entry(history_file):
    entry = record_snapshot("snap1", "/tmp/snap1.json", history_path=history_file)
    assert isinstance(entry, HistoryEntry)
    assert entry.snapshot_name == "snap1"
    assert entry.path == "/tmp/snap1.json"


def test_record_snapshot_persists_to_file(history_file):
    record_snapshot("snap1", "/tmp/snap1.json", history_path=history_file)
    p = Path(history_file)
    assert p.exists()
    data = json.loads(p.read_text())
    assert len(data) == 1
    assert data[0]["snapshot_name"] == "snap1"


def test_multiple_records_appended(history_file):
    record_snapshot("snap1", "/tmp/snap1.json", history_path=history_file)
    record_snapshot("snap2", "/tmp/snap2.json", history_path=history_file)
    entries = load_history(history_file)
    assert len(entries) == 2
    assert entries[0].snapshot_name == "snap1"
    assert entries[1].snapshot_name == "snap2"


def test_record_stores_tags(history_file):
    entry = record_snapshot("snap1", "/tmp/snap1.json", tags=["prod", "release"], history_path=history_file)
    assert "prod" in entry.tags
    assert "release" in entry.tags


def test_record_deduplicates_tags(history_file):
    entry = record_snapshot("snap1", "/tmp/snap1.json", tags=["prod", "prod"], history_path=history_file)
    assert entry.tags.count("prod") == 1


def test_record_stores_note(history_file):
    entry = record_snapshot("snap1", "/tmp/snap1.json", note="initial deploy", history_path=history_file)
    assert entry.note == "initial deploy"


def test_record_has_timestamp(history_file):
    entry = record_snapshot("snap1", "/tmp/snap1.json", history_path=history_file)
    assert entry.timestamp
    assert "T" in entry.timestamp  # ISO format


def test_load_returns_empty_when_no_file(tmp_path):
    entries = load_history(str(tmp_path / "nonexistent.json"))
    assert entries == []


def test_find_by_tag_returns_matching(history_file):
    record_snapshot("snap1", "/tmp/snap1.json", tags=["prod"], history_path=history_file)
    record_snapshot("snap2", "/tmp/snap2.json", tags=["staging"], history_path=history_file)
    results = find_by_tag("prod", history_path=history_file)
    assert len(results) == 1
    assert results[0].snapshot_name == "snap1"


def test_find_by_name_returns_matching(history_file):
    record_snapshot("snap1", "/tmp/snap1.json", history_path=history_file)
    record_snapshot("snap1", "/tmp/snap1_v2.json", history_path=history_file)
    record_snapshot("snap2", "/tmp/snap2.json", history_path=history_file)
    results = find_by_name("snap1", history_path=history_file)
    assert len(results) == 2


def test_clear_history_empties_file(history_file):
    record_snapshot("snap1", "/tmp/snap1.json", history_path=history_file)
    clear_history(history_file)
    entries = load_history(history_file)
    assert entries == []
