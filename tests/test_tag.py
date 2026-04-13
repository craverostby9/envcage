"""Tests for envcage.tag module."""

import json
import pytest
from pathlib import Path

from envcage.tag import (
    add_tag,
    remove_tag,
    get_tags,
    find_by_tag,
    list_all_tags,
)


@pytest.fixture
def tag_file(tmp_path):
    return str(tmp_path / "tags.json")


def test_add_tag_creates_entry(tag_file):
    add_tag("snap_a", "production", tag_file)
    assert "production" in get_tags("snap_a", tag_file)


def test_add_tag_duplicate_ignored(tag_file):
    add_tag("snap_a", "production", tag_file)
    add_tag("snap_a", "production", tag_file)
    assert get_tags("snap_a", tag_file).count("production") == 1


def test_add_multiple_tags(tag_file):
    add_tag("snap_a", "production", tag_file)
    add_tag("snap_a", "v2", tag_file)
    tags = get_tags("snap_a", tag_file)
    assert "production" in tags
    assert "v2" in tags


def test_tags_are_sorted(tag_file):
    add_tag("snap_a", "zebra", tag_file)
    add_tag("snap_a", "alpha", tag_file)
    assert get_tags("snap_a", tag_file) == ["alpha", "zebra"]


def test_remove_tag(tag_file):
    add_tag("snap_a", "production", tag_file)
    remove_tag("snap_a", "production", tag_file)
    assert "production" not in get_tags("snap_a", tag_file)


def test_remove_nonexistent_tag_is_noop(tag_file):
    add_tag("snap_a", "production", tag_file)
    remove_tag("snap_a", "staging", tag_file)  # should not raise
    assert get_tags("snap_a", tag_file) == ["production"]


def test_remove_last_tag_cleans_entry(tag_file):
    add_tag("snap_a", "production", tag_file)
    remove_tag("snap_a", "production", tag_file)
    store = list_all_tags(tag_file)
    assert "snap_a" not in store


def test_get_tags_returns_empty_for_unknown_snapshot(tag_file):
    assert get_tags("nonexistent", tag_file) == []


def test_find_by_tag_returns_matching_snapshots(tag_file):
    add_tag("snap_a", "production", tag_file)
    add_tag("snap_b", "production", tag_file)
    add_tag("snap_c", "staging", tag_file)
    result = find_by_tag("production", tag_file)
    assert result == ["snap_a", "snap_b"]
    assert "snap_c" not in result


def test_find_by_tag_returns_empty_when_none_match(tag_file):
    add_tag("snap_a", "staging", tag_file)
    assert find_by_tag("production", tag_file) == []


def test_list_all_tags_returns_full_store(tag_file):
    add_tag("snap_a", "production", tag_file)
    add_tag("snap_b", "staging", tag_file)
    store = list_all_tags(tag_file)
    assert "snap_a" in store
    assert "snap_b" in store


def test_tag_store_persisted_as_valid_json(tag_file):
    add_tag("snap_a", "production", tag_file)
    with open(tag_file) as f:
        data = json.load(f)
    assert isinstance(data, dict)
