"""Tests for envcage.env_snapshot_index."""
import json
import os
import pytest

from envcage.env_snapshot_index import (
    IndexEntry,
    index_snapshot,
    remove_from_index,
    get_index_entry,
    list_index,
    search_index,
)


@pytest.fixture()
def idx(tmp_path):
    return str(tmp_path / "index.json")


# --- IndexEntry serialisation ---

def test_to_dict_round_trips():
    e = IndexEntry(name="prod", path="/snaps/prod.json", key_count=10, tags=["live"], description="Production")
    assert IndexEntry.from_dict(e.to_dict()) == e


def test_from_dict_defaults():
    e = IndexEntry.from_dict({"name": "dev", "path": "dev.json", "key_count": 3})
    assert e.tags == []
    assert e.description == ""


# --- index_snapshot ---

def test_index_snapshot_creates_file(idx):
    index_snapshot("dev", "dev.json", 5, index_file=idx)
    assert os.path.exists(idx)


def test_index_snapshot_file_is_valid_json(idx):
    index_snapshot("dev", "dev.json", 5, index_file=idx)
    with open(idx) as fh:
        data = json.load(fh)
    assert "dev" in data


def test_index_snapshot_stores_key_count(idx):
    entry = index_snapshot("dev", "dev.json", 42, index_file=idx)
    assert entry.key_count == 42


def test_index_snapshot_stores_tags(idx):
    entry = index_snapshot("dev", "dev.json", 3, tags=["beta", "alpha"], index_file=idx)
    assert entry.tags == ["alpha", "beta"]  # sorted


def test_index_snapshot_deduplicates_tags(idx):
    entry = index_snapshot("dev", "dev.json", 3, tags=["x", "x"], index_file=idx)
    assert entry.tags == ["x"]


def test_index_snapshot_overwrites_existing(idx):
    index_snapshot("dev", "dev.json", 3, index_file=idx)
    entry = index_snapshot("dev", "dev.json", 99, index_file=idx)
    assert entry.key_count == 99
    assert get_index_entry("dev", index_file=idx).key_count == 99


# --- remove_from_index ---

def test_remove_returns_true_when_found(idx):
    index_snapshot("dev", "dev.json", 3, index_file=idx)
    assert remove_from_index("dev", index_file=idx) is True


def test_remove_returns_false_when_missing(idx):
    assert remove_from_index("ghost", index_file=idx) is False


def test_remove_entry_no_longer_listed(idx):
    index_snapshot("dev", "dev.json", 3, index_file=idx)
    remove_from_index("dev", index_file=idx)
    assert get_index_entry("dev", index_file=idx) is None


# --- list_index ---

def test_list_index_empty_when_no_file(idx):
    assert list_index(index_file=idx) == []


def test_list_index_returns_all_entries(idx):
    index_snapshot("b", "b.json", 1, index_file=idx)
    index_snapshot("a", "a.json", 2, index_file=idx)
    names = [e.name for e in list_index(index_file=idx)]
    assert names == ["a", "b"]  # sorted


# --- search_index ---

def test_search_finds_by_name_substring(idx):
    index_snapshot("production", "prod.json", 10, index_file=idx)
    index_snapshot("staging", "stage.json", 5, index_file=idx)
    results = search_index("prod", index_file=idx)
    assert len(results) == 1
    assert results[0].name == "production"


def test_search_finds_by_description(idx):
    index_snapshot("x", "x.json", 1, description="live environment", index_file=idx)
    index_snapshot("y", "y.json", 1, description="testing only", index_file=idx)
    results = search_index("live", index_file=idx)
    assert results[0].name == "x"


def test_search_case_insensitive_by_default(idx):
    index_snapshot("Prod", "prod.json", 1, index_file=idx)
    assert len(search_index("prod", index_file=idx)) == 1


def test_search_case_sensitive_no_match(idx):
    index_snapshot("Prod", "prod.json", 1, index_file=idx)
    assert search_index("prod", index_file=idx, case_sensitive=True) == []


def test_search_returns_empty_when_no_match(idx):
    index_snapshot("dev", "dev.json", 1, index_file=idx)
    assert search_index("zzz", index_file=idx) == []
