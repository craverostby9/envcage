"""Tests for envcage.env_snapshot_notes."""
import json
import pytest
from pathlib import Path

from envcage.env_snapshot_notes import (
    add_note,
    get_notes,
    remove_notes,
    list_noted_snapshots,
    all_notes,
)


@pytest.fixture
def nf(tmp_path):
    return str(tmp_path / "notes.json")


def test_add_note_creates_file(nf):
    add_note("snap_a", "first note", notes_file=nf)
    assert Path(nf).exists()


def test_add_note_file_is_valid_json(nf):
    add_note("snap_a", "hello", notes_file=nf)
    data = json.loads(Path(nf).read_text())
    assert isinstance(data, dict)


def test_add_note_persists(nf):
    add_note("snap_a", "my note", notes_file=nf)
    notes = get_notes("snap_a", notes_file=nf)
    assert "my note" in notes


def test_add_multiple_notes_appended(nf):
    add_note("snap_a", "note one", notes_file=nf)
    add_note("snap_a", "note two", notes_file=nf)
    notes = get_notes("snap_a", notes_file=nf)
    assert notes == ["note one", "note two"]


def test_get_notes_returns_empty_list_when_missing(nf):
    notes = get_notes("nonexistent", notes_file=nf)
    assert notes == []


def test_get_notes_returns_empty_when_no_file(nf):
    # file doesn't exist at all
    assert get_notes("snap_x", notes_file=nf) == []


def test_notes_for_different_snapshots_isolated(nf):
    add_note("snap_a", "alpha", notes_file=nf)
    add_note("snap_b", "beta", notes_file=nf)
    assert get_notes("snap_a", notes_file=nf) == ["alpha"]
    assert get_notes("snap_b", notes_file=nf) == ["beta"]


def test_remove_notes_returns_count(nf):
    add_note("snap_a", "n1", notes_file=nf)
    add_note("snap_a", "n2", notes_file=nf)
    count = remove_notes("snap_a", notes_file=nf)
    assert count == 2


def test_remove_notes_clears_snapshot(nf):
    add_note("snap_a", "gone", notes_file=nf)
    remove_notes("snap_a", notes_file=nf)
    assert get_notes("snap_a", notes_file=nf) == []


def test_remove_notes_missing_snapshot_returns_zero(nf):
    count = remove_notes("ghost", notes_file=nf)
    assert count == 0


def test_list_noted_snapshots_sorted(nf):
    add_note("snap_z", "z", notes_file=nf)
    add_note("snap_a", "a", notes_file=nf)
    add_note("snap_m", "m", notes_file=nf)
    assert list_noted_snapshots(notes_file=nf) == ["snap_a", "snap_m", "snap_z"]


def test_list_noted_snapshots_empty_when_no_file(nf):
    assert list_noted_snapshots(notes_file=nf) == []


def test_all_notes_returns_full_store(nf):
    add_note("s1", "foo", notes_file=nf)
    add_note("s2", "bar", notes_file=nf)
    store = all_notes(notes_file=nf)
    assert store == {"s1": ["foo"], "s2": ["bar"]}
