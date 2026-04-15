"""Tests for envcage.env_alias."""
import json
import pytest
from pathlib import Path

from envcage.env_alias import (
    set_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
    aliases_for_snapshot,
)


@pytest.fixture
def af(tmp_path) -> str:
    return str(tmp_path / "aliases.json")


def test_set_alias_creates_file(af):
    set_alias("prod", "snapshots/prod.json", af)
    assert Path(af).exists()


def test_set_alias_file_is_valid_json(af):
    set_alias("prod", "snapshots/prod.json", af)
    data = json.loads(Path(af).read_text())
    assert "aliases" in data


def test_set_alias_persists(af):
    set_alias("prod", "snapshots/prod.json", af)
    assert resolve_alias("prod", af) == "snapshots/prod.json"


def test_set_alias_overwrites_existing(af):
    set_alias("prod", "old.json", af)
    set_alias("prod", "new.json", af)
    assert resolve_alias("prod", af) == "new.json"


def test_resolve_alias_returns_none_when_missing(af):
    assert resolve_alias("nonexistent", af) is None


def test_remove_alias_returns_true_when_found(af):
    set_alias("staging", "staging.json", af)
    assert remove_alias("staging", af) is True


def test_remove_alias_returns_false_when_missing(af):
    assert remove_alias("ghost", af) is False


def test_remove_alias_actually_removes(af):
    set_alias("staging", "staging.json", af)
    remove_alias("staging", af)
    assert resolve_alias("staging", af) is None


def test_list_aliases_returns_all(af):
    set_alias("prod", "prod.json", af)
    set_alias("dev", "dev.json", af)
    result = list_aliases(af)
    assert result == {"prod": "prod.json", "dev": "dev.json"}


def test_list_aliases_empty_when_no_file(af):
    assert list_aliases(af) == {}


def test_aliases_for_snapshot_finds_multiple(af):
    set_alias("prod", "shared.json", af)
    set_alias("live", "shared.json", af)
    set_alias("dev", "other.json", af)
    result = aliases_for_snapshot("shared.json", af)
    assert result == ["live", "prod"]


def test_aliases_for_snapshot_empty_when_none_match(af):
    set_alias("prod", "prod.json", af)
    assert aliases_for_snapshot("missing.json", af) == []
