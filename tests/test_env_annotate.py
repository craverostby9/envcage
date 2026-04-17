"""Tests for envcage.env_annotate."""
import json
import pytest
from envcage.env_annotate import (
    set_annotation,
    get_annotation,
    remove_annotation,
    list_annotations,
    all_annotations,
)


@pytest.fixture
def af(tmp_path):
    return str(tmp_path / "annotations.json")


def test_set_annotation_creates_file(af):
    set_annotation("snap.json", "DB_HOST", "primary host", af)
    import os
    assert os.path.exists(af)


def test_set_annotation_file_is_valid_json(af):
    set_annotation("snap.json", "DB_HOST", "primary host", af)
    with open(af) as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_get_annotation_returns_note(af):
    set_annotation("snap.json", "DB_HOST", "primary host", af)
    note = get_annotation("snap.json", "DB_HOST", af)
    assert note == "primary host"


def test_get_annotation_returns_none_when_missing(af):
    result = get_annotation("snap.json", "MISSING_KEY", af)
    assert result is None


def test_set_annotation_overwrites_existing(af):
    set_annotation("snap.json", "DB_HOST", "old note", af)
    set_annotation("snap.json", "DB_HOST", "new note", af)
    assert get_annotation("snap.json", "DB_HOST", af) == "new note"


def test_remove_annotation_returns_true_when_found(af):
    set_annotation("snap.json", "API_KEY", "secret", af)
    result = remove_annotation("snap.json", "API_KEY", af)
    assert result is True


def test_remove_annotation_key_gone_after_removal(af):
    set_annotation("snap.json", "API_KEY", "secret", af)
    remove_annotation("snap.json", "API_KEY", af)
    assert get_annotation("snap.json", "API_KEY", af) is None


def test_remove_annotation_returns_false_when_missing(af):
    result = remove_annotation("snap.json", "NONEXISTENT", af)
    assert result is False


def test_list_annotations_returns_all_for_snapshot(af):
    set_annotation("snap.json", "DB_HOST", "host note", af)
    set_annotation("snap.json", "DB_PORT", "port note", af)
    result = list_annotations("snap.json", af)
    assert result == {"DB_HOST": "host note", "DB_PORT": "port note"}


def test_list_annotations_empty_when_no_file(af):
    result = list_annotations("snap.json", af)
    assert result == {}


def test_list_annotations_isolated_per_snapshot(af):
    set_annotation("snap_a.json", "KEY", "note a", af)
    set_annotation("snap_b.json", "KEY", "note b", af)
    assert list_annotations("snap_a.json", af) == {"KEY": "note a"}
    assert list_annotations("snap_b.json", af) == {"KEY": "note b"}


def test_all_annotations_returns_full_store(af):
    set_annotation("snap_a.json", "X", "xa", af)
    set_annotation("snap_b.json", "Y", "yb", af)
    store = all_annotations(af)
    assert "snap_a.json" in store
    assert "snap_b.json" in store
