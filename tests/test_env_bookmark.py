"""Tests for envcage.env_bookmark."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.env_bookmark import (
    Bookmark,
    get_bookmark,
    list_bookmarks,
    remove_bookmark,
    set_bookmark,
)


@pytest.fixture()
def bf(tmp_path: Path) -> Path:
    return tmp_path / "bookmarks.json"


def test_set_bookmark_creates_file(bf: Path) -> None:
    set_bookmark("prod", "snapshots/prod.json", store_path=bf)
    assert bf.exists()


def test_set_bookmark_file_is_valid_json(bf: Path) -> None:
    set_bookmark("prod", "snapshots/prod.json", store_path=bf)
    data = json.loads(bf.read_text())
    assert isinstance(data, dict)


def test_set_bookmark_persists_name(bf: Path) -> None:
    set_bookmark("staging", "snapshots/staging.json", store_path=bf)
    bm = get_bookmark("staging", store_path=bf)
    assert bm is not None
    assert bm.name == "staging"


def test_set_bookmark_persists_snapshot_path(bf: Path) -> None:
    set_bookmark("dev", "snapshots/dev.json", store_path=bf)
    bm = get_bookmark("dev", store_path=bf)
    assert bm is not None
    assert bm.snapshot_path == "snapshots/dev.json"


def test_set_bookmark_persists_description(bf: Path) -> None:
    set_bookmark("prod", "snapshots/prod.json", description="Production env", store_path=bf)
    bm = get_bookmark("prod", store_path=bf)
    assert bm is not None
    assert bm.description == "Production env"


def test_set_bookmark_overwrites_existing(bf: Path) -> None:
    set_bookmark("prod", "old.json", store_path=bf)
    set_bookmark("prod", "new.json", store_path=bf)
    bm = get_bookmark("prod", store_path=bf)
    assert bm is not None
    assert bm.snapshot_path == "new.json"


def test_get_bookmark_returns_none_when_missing(bf: Path) -> None:
    assert get_bookmark("nonexistent", store_path=bf) is None


def test_remove_bookmark_returns_true_when_exists(bf: Path) -> None:
    set_bookmark("temp", "snap.json", store_path=bf)
    assert remove_bookmark("temp", store_path=bf) is True


def test_remove_bookmark_returns_false_when_missing(bf: Path) -> None:
    assert remove_bookmark("ghost", store_path=bf) is False


def test_remove_bookmark_deletes_entry(bf: Path) -> None:
    set_bookmark("temp", "snap.json", store_path=bf)
    remove_bookmark("temp", store_path=bf)
    assert get_bookmark("temp", store_path=bf) is None


def test_list_bookmarks_empty_when_no_file(bf: Path) -> None:
    assert list_bookmarks(store_path=bf) == []


def test_list_bookmarks_returns_all(bf: Path) -> None:
    set_bookmark("b", "b.json", store_path=bf)
    set_bookmark("a", "a.json", store_path=bf)
    bms = list_bookmarks(store_path=bf)
    assert len(bms) == 2


def test_list_bookmarks_sorted_by_name(bf: Path) -> None:
    set_bookmark("z_snap", "z.json", store_path=bf)
    set_bookmark("a_snap", "a.json", store_path=bf)
    set_bookmark("m_snap", "m.json", store_path=bf)
    names = [bm.name for bm in list_bookmarks(store_path=bf)]
    assert names == sorted(names)


def test_to_dict_round_trips() -> None:
    bm = Bookmark(name="x", snapshot_path="x.json", description="desc")
    restored = Bookmark.from_dict(bm.to_dict())
    assert restored.name == bm.name
    assert restored.snapshot_path == bm.snapshot_path
    assert restored.description == bm.description
