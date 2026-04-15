"""Tests for envcage.scope."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.scope import (
    Scope,
    add_snapshot_to_scope,
    create_scope,
    delete_scope,
    list_scopes,
    load_scope,
    remove_snapshot_from_scope,
    save_scope,
)


@pytest.fixture()
def sf(tmp_path: Path) -> Path:
    return tmp_path / "scopes.json"


def test_create_scope_stores_name():
    s = create_scope("production")
    assert s.name == "production"


def test_create_scope_stores_description():
    s = create_scope("staging", description="Staging environment")
    assert s.description == "Staging environment"


def test_create_scope_empty_snapshots_by_default():
    s = create_scope("dev")
    assert s.snapshots == []


def test_save_creates_file(sf):
    save_scope(create_scope("prod"), sf)
    assert sf.exists()


def test_save_file_is_valid_json(sf):
    save_scope(create_scope("prod"), sf)
    data = json.loads(sf.read_text())
    assert "prod" in data


def test_load_returns_none_when_missing(sf):
    assert load_scope("ghost", sf) is None


def test_load_returns_saved_scope(sf):
    s = Scope(name="prod", description="Production", snapshots=["snap_a.json"])
    save_scope(s, sf)
    loaded = load_scope("prod", sf)
    assert loaded is not None
    assert loaded.name == "prod"
    assert loaded.description == "Production"
    assert loaded.snapshots == ["snap_a.json"]


def test_add_snapshot_to_scope_persists(sf):
    add_snapshot_to_scope("prod", "snap1.json", sf)
    scope = load_scope("prod", sf)
    assert "snap1.json" in scope.snapshots


def test_add_snapshot_duplicate_ignored(sf):
    add_snapshot_to_scope("prod", "snap1.json", sf)
    add_snapshot_to_scope("prod", "snap1.json", sf)
    scope = load_scope("prod", sf)
    assert scope.snapshots.count("snap1.json") == 1


def test_add_snapshot_sorted(sf):
    add_snapshot_to_scope("prod", "z_snap.json", sf)
    add_snapshot_to_scope("prod", "a_snap.json", sf)
    scope = load_scope("prod", sf)
    assert scope.snapshots == sorted(scope.snapshots)


def test_remove_snapshot_from_scope(sf):
    add_snapshot_to_scope("prod", "snap1.json", sf)
    remove_snapshot_from_scope("prod", "snap1.json", sf)
    scope = load_scope("prod", sf)
    assert "snap1.json" not in scope.snapshots


def test_list_scopes_returns_sorted(sf):
    save_scope(create_scope("z_scope"), sf)
    save_scope(create_scope("a_scope"), sf)
    names = list_scopes(sf)
    assert names == sorted(names)


def test_delete_scope_removes_entry(sf):
    save_scope(create_scope("temp"), sf)
    result = delete_scope("temp", sf)
    assert result is True
    assert load_scope("temp", sf) is None


def test_delete_scope_missing_returns_false(sf):
    assert delete_scope("nonexistent", sf) is False
