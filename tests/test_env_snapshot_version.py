"""Tests for envcage.env_snapshot_version."""
import json
from pathlib import Path

import pytest

from envcage.env_snapshot_version import (
    VersionEntry,
    find_by_version,
    get_version,
    list_versions,
    remove_version,
    set_version,
)


@pytest.fixture()
def vf(tmp_path):
    return str(tmp_path / "versions.json")


def test_set_version_creates_file(vf):
    set_version("snap.json", "1.0.0", store_path=vf)
    assert Path(vf).exists()


def test_set_version_file_is_valid_json(vf):
    set_version("snap.json", "1.0.0", store_path=vf)
    data = json.loads(Path(vf).read_text())
    assert isinstance(data, dict)


def test_set_version_persists_version(vf):
    set_version("snap.json", "2.1.0", store_path=vf)
    entry = get_version("snap.json", store_path=vf)
    assert entry is not None
    assert entry.version == "2.1.0"


def test_set_version_persists_label(vf):
    set_version("snap.json", "1.0.0", label="production", store_path=vf)
    entry = get_version("snap.json", store_path=vf)
    assert entry.label == "production"


def test_set_version_persists_note(vf):
    set_version("snap.json", "1.0.0", note="initial release", store_path=vf)
    entry = get_version("snap.json", store_path=vf)
    assert entry.note == "initial release"


def test_set_version_overwrites_existing(vf):
    set_version("snap.json", "1.0.0", store_path=vf)
    set_version("snap.json", "1.1.0", store_path=vf)
    entry = get_version("snap.json", store_path=vf)
    assert entry.version == "1.1.0"


def test_get_version_returns_none_when_missing(vf):
    assert get_version("nonexistent.json", store_path=vf) is None


def test_remove_version_removes_entry(vf):
    set_version("snap.json", "1.0.0", store_path=vf)
    removed = remove_version("snap.json", store_path=vf)
    assert removed is True
    assert get_version("snap.json", store_path=vf) is None


def test_remove_version_returns_false_when_missing(vf):
    assert remove_version("ghost.json", store_path=vf) is False


def test_list_versions_returns_all(vf):
    set_version("a.json", "1.0.0", store_path=vf)
    set_version("b.json", "2.0.0", store_path=vf)
    entries = list_versions(store_path=vf)
    assert len(entries) == 2


def test_list_versions_empty_when_no_file(vf):
    assert list_versions(store_path=vf) == []


def test_find_by_version_matches(vf):
    set_version("a.json", "1.0.0", store_path=vf)
    set_version("b.json", "1.0.0", store_path=vf)
    set_version("c.json", "2.0.0", store_path=vf)
    results = find_by_version("1.0.0", store_path=vf)
    assert len(results) == 2
    assert all(e.version == "1.0.0" for e in results)


def test_find_by_version_no_match(vf):
    set_version("a.json", "1.0.0", store_path=vf)
    assert find_by_version("9.9.9", store_path=vf) == []


def test_to_dict_round_trips():
    entry = VersionEntry(snapshot="s.json", version="3.0.0", label="staging", note="test")
    restored = VersionEntry.from_dict(entry.to_dict())
    assert restored.snapshot == entry.snapshot
    assert restored.version == entry.version
    assert restored.label == entry.label
    assert restored.note == entry.note
