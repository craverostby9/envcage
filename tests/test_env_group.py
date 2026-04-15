"""Tests for envcage.env_group."""
import json
import pytest
from pathlib import Path

from envcage.env_group import (
    EnvGroup,
    add_snapshot_to_group,
    create_group,
    delete_group,
    list_groups,
    load_group,
    remove_snapshot_from_group,
    save_group,
)


@pytest.fixture()
def gf(tmp_path: Path) -> Path:
    return tmp_path / "groups.json"


# ---------- create_group ----------

def test_create_group_stores_name():
    g = create_group("production")
    assert g.name == "production"


def test_create_group_stores_description():
    g = create_group("staging", description="Staging envs")
    assert g.description == "Staging envs"


def test_create_group_deduplicates_and_sorts_snapshots():
    g = create_group("prod", snapshots=["b.json", "a.json", "a.json"])
    assert g.snapshots == ["a.json", "b.json"]


def test_create_group_empty_snapshots_by_default():
    g = create_group("empty")
    assert g.snapshots == []


# ---------- save / load ----------

def test_save_creates_file(gf):
    save_group(create_group("prod"), gf)
    assert gf.exists()


def test_save_file_is_valid_json(gf):
    save_group(create_group("prod", description="x"), gf)
    data = json.loads(gf.read_text())
    assert "prod" in data


def test_load_returns_group(gf):
    save_group(create_group("dev", description="Dev group", snapshots=["s.json"]), gf)
    g = load_group("dev", gf)
    assert g is not None
    assert g.name == "dev"
    assert g.description == "Dev group"
    assert "s.json" in g.snapshots


def test_load_returns_none_when_missing(gf):
    assert load_group("nope", gf) is None


# ---------- list_groups ----------

def test_list_groups_returns_sorted_names(gf):
    save_group(create_group("z-group"), gf)
    save_group(create_group("a-group"), gf)
    assert list_groups(gf) == ["a-group", "z-group"]


def test_list_groups_empty_store(gf):
    assert list_groups(gf) == []


# ---------- add / remove snapshot ----------

def test_add_snapshot_to_group_persists(gf):
    add_snapshot_to_group("prod", "snap1.json", gf)
    g = load_group("prod", gf)
    assert "snap1.json" in g.snapshots


def test_add_snapshot_duplicate_ignored(gf):
    add_snapshot_to_group("prod", "snap1.json", gf)
    add_snapshot_to_group("prod", "snap1.json", gf)
    g = load_group("prod", gf)
    assert g.snapshots.count("snap1.json") == 1


def test_remove_snapshot_from_group(gf):
    add_snapshot_to_group("prod", "snap1.json", gf)
    add_snapshot_to_group("prod", "snap2.json", gf)
    remove_snapshot_from_group("prod", "snap1.json", gf)
    g = load_group("prod", gf)
    assert "snap1.json" not in g.snapshots
    assert "snap2.json" in g.snapshots


def test_remove_snapshot_missing_group_returns_none(gf):
    result = remove_snapshot_from_group("ghost", "snap.json", gf)
    assert result is None


# ---------- delete_group ----------

def test_delete_group_removes_entry(gf):
    save_group(create_group("temp"), gf)
    assert delete_group("temp", gf) is True
    assert load_group("temp", gf) is None


def test_delete_group_returns_false_when_missing(gf):
    assert delete_group("ghost", gf) is False
