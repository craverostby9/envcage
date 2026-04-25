"""Tests for envcage.env_lineage."""
import json
import pytest
from pathlib import Path

from envcage.env_lineage import (
    LineageNode,
    link_snapshot,
    get_lineage,
    ancestors,
    descendants,
    remove_lineage,
)


@pytest.fixture()
def lf(tmp_path) -> str:
    return str(tmp_path / "lineage.json")


# ---------------------------------------------------------------------------
# LineageNode serialisation
# ---------------------------------------------------------------------------

def test_to_dict_round_trips():
    node = LineageNode(snapshot="snap_b", parent="snap_a", children=["snap_c"], note="promoted")
    restored = LineageNode.from_dict(node.to_dict())
    assert restored.snapshot == "snap_b"
    assert restored.parent == "snap_a"
    assert restored.children == ["snap_c"]
    assert restored.note == "promoted"


def test_from_dict_defaults():
    node = LineageNode.from_dict({"snapshot": "x"})
    assert node.parent is None
    assert node.children == []
    assert node.note == ""


# ---------------------------------------------------------------------------
# link_snapshot
# ---------------------------------------------------------------------------

def test_link_snapshot_creates_file(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    assert Path(lf).exists()


def test_link_snapshot_file_is_valid_json(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    data = json.loads(Path(lf).read_text())
    assert isinstance(data, dict)


def test_link_snapshot_sets_parent(lf):
    node = link_snapshot("child", "parent", lineage_file=lf)
    assert node.parent == "parent"


def test_link_snapshot_registers_child_on_parent(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    parent_node = get_lineage("parent", lineage_file=lf)
    assert "child" in parent_node.children


def test_link_snapshot_stores_note(lf):
    link_snapshot("child", "parent", note="staging promote", lineage_file=lf)
    node = get_lineage("child", lineage_file=lf)
    assert node.note == "staging promote"


def test_link_snapshot_duplicate_child_not_repeated(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    link_snapshot("child", "parent", lineage_file=lf)
    parent_node = get_lineage("parent", lineage_file=lf)
    assert parent_node.children.count("child") == 1


# ---------------------------------------------------------------------------
# get_lineage
# ---------------------------------------------------------------------------

def test_get_lineage_returns_none_when_missing(lf):
    assert get_lineage("nonexistent", lineage_file=lf) is None


def test_get_lineage_returns_node(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    node = get_lineage("child", lineage_file=lf)
    assert isinstance(node, LineageNode)


# ---------------------------------------------------------------------------
# ancestors
# ---------------------------------------------------------------------------

def test_ancestors_empty_when_no_parent(lf):
    link_snapshot("child", "root", lineage_file=lf)
    assert ancestors("root", lineage_file=lf) == []


def test_ancestors_returns_chain(lf):
    link_snapshot("b", "a", lineage_file=lf)
    link_snapshot("c", "b", lineage_file=lf)
    result = ancestors("c", lineage_file=lf)
    assert result == ["a", "b"]


def test_ancestors_single_level(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    result = ancestors("child", lineage_file=lf)
    assert result == ["parent"]


# ---------------------------------------------------------------------------
# descendants
# ---------------------------------------------------------------------------

def test_descendants_empty_when_no_children(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    assert descendants("child", lineage_file=lf) == []


def test_descendants_returns_direct_children(lf):
    link_snapshot("b", "a", lineage_file=lf)
    link_snapshot("c", "a", lineage_file=lf)
    result = descendants("a", lineage_file=lf)
    assert set(result) == {"b", "c"}


def test_descendants_recursive(lf):
    link_snapshot("b", "a", lineage_file=lf)
    link_snapshot("c", "b", lineage_file=lf)
    result = descendants("a", lineage_file=lf)
    assert "b" in result and "c" in result


# ---------------------------------------------------------------------------
# remove_lineage
# ---------------------------------------------------------------------------

def test_remove_lineage_returns_false_when_missing(lf):
    assert remove_lineage("ghost", lineage_file=lf) is False


def test_remove_lineage_returns_true_when_exists(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    assert remove_lineage("child", lineage_file=lf) is True


def test_remove_lineage_cleans_parent_children(lf):
    link_snapshot("child", "parent", lineage_file=lf)
    remove_lineage("child", lineage_file=lf)
    parent_node = get_lineage("parent", lineage_file=lf)
    assert "child" not in (parent_node.children if parent_node else [])
