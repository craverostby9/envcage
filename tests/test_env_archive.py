"""Tests for envcage.env_archive."""
import json
from pathlib import Path

import pytest

from envcage.env_archive import (
    ArchiveEntry,
    archive_snapshot,
    list_archived,
    restore_snapshot,
)


@pytest.fixture()
def snap_file(tmp_path: Path) -> Path:
    p = tmp_path / "snap.json"
    p.write_text(json.dumps({"env": {"FOO": "bar"}, "required": [], "timestamp": "t"}))
    return p


@pytest.fixture()
def archive_dir(tmp_path: Path) -> Path:
    return tmp_path / "archive"


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    return tmp_path / "archive_log.json"


def test_archive_moves_file(snap_file, archive_dir, log_file):
    archive_snapshot(snap_file, archive_dir, log_file)
    assert not snap_file.exists()
    assert (archive_dir / "snap.json").exists()


def test_archive_returns_entry(snap_file, archive_dir, log_file):
    entry = archive_snapshot(snap_file, archive_dir, log_file, reason="cleanup")
    assert isinstance(entry, ArchiveEntry)
    assert entry.snapshot == "snap.json"
    assert entry.reason == "cleanup"


def test_archive_creates_log(snap_file, archive_dir, log_file):
    archive_snapshot(snap_file, archive_dir, log_file)
    assert log_file.exists()


def test_archive_log_is_valid_json(snap_file, archive_dir, log_file):
    archive_snapshot(snap_file, archive_dir, log_file)
    data = json.loads(log_file.read_text())
    assert isinstance(data, list)
    assert len(data) == 1


def test_archive_log_stores_reason(snap_file, archive_dir, log_file):
    archive_snapshot(snap_file, archive_dir, log_file, reason="old release")
    data = json.loads(log_file.read_text())
    assert data[0]["reason"] == "old release"


def test_multiple_archives_appended(tmp_path, archive_dir, log_file):
    for name in ("a.json", "b.json"):
        p = tmp_path / name
        p.write_text(json.dumps({"env": {}, "required": [], "timestamp": "t"}))
        archive_snapshot(p, archive_dir, log_file)
    entries = list_archived(log_file)
    assert len(entries) == 2


def test_list_archived_empty_when_no_log(log_file):
    assert list_archived(log_file) == []


def test_restore_snapshot_copies_file(snap_file, archive_dir, log_file, tmp_path):
    archive_snapshot(snap_file, archive_dir, log_file)
    restore_dir = tmp_path / "restored"
    dest = restore_snapshot("snap.json", archive_dir, restore_dir, log_file)
    assert dest.exists()


def test_restore_snapshot_returns_path(snap_file, archive_dir, log_file, tmp_path):
    archive_snapshot(snap_file, archive_dir, log_file)
    restore_dir = tmp_path / "restored"
    dest = restore_snapshot("snap.json", archive_dir, restore_dir, log_file)
    assert isinstance(dest, Path)
    assert dest.name == "snap.json"


def test_restore_missing_raises(archive_dir, log_file, tmp_path):
    with pytest.raises(FileNotFoundError):
        restore_snapshot("ghost.json", archive_dir, tmp_path / "r", log_file)


def test_to_dict_round_trips():
    e = ArchiveEntry(snapshot="s.json", archived_at="2024-01-01T00:00:00", reason="test", archive_path="/a/s.json")
    assert ArchiveEntry.from_dict(e.to_dict()).snapshot == "s.json"
    assert ArchiveEntry.from_dict(e.to_dict()).reason == "test"
