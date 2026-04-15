"""Tests for envcage.cli_scope."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envcage.cli_scope import (
    cmd_scope_add,
    cmd_scope_create,
    cmd_scope_delete,
    cmd_scope_list,
    cmd_scope_remove,
    cmd_scope_show,
)
from envcage.scope import add_snapshot_to_scope, load_scope, save_scope, create_scope


def _args(sf: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(scope_file=str(sf), **kwargs)


@pytest.fixture()
def sf(tmp_path: Path) -> Path:
    return tmp_path / "scopes.json"


def test_cmd_scope_create_writes_file(sf, capsys):
    cmd_scope_create(_args(sf, name="prod", description=""))
    assert sf.exists()


def test_cmd_scope_create_prints_confirmation(sf, capsys):
    cmd_scope_create(_args(sf, name="staging", description=""))
    out = capsys.readouterr().out
    assert "staging" in out


def test_cmd_scope_add_persists_snapshot(sf, capsys):
    cmd_scope_add(_args(sf, name="prod", snapshot="snap1.json"))
    scope = load_scope("prod", sf)
    assert "snap1.json" in scope.snapshots


def test_cmd_scope_add_prints_total(sf, capsys):
    cmd_scope_add(_args(sf, name="prod", snapshot="snap1.json"))
    out = capsys.readouterr().out
    assert "1" in out


def test_cmd_scope_remove_removes_snapshot(sf, capsys):
    add_snapshot_to_scope("prod", "snap1.json", sf)
    cmd_scope_remove(_args(sf, name="prod", snapshot="snap1.json"))
    scope = load_scope("prod", sf)
    assert "snap1.json" not in scope.snapshots


def test_cmd_scope_show_prints_name(sf, capsys):
    save_scope(create_scope("prod", description="Production"), sf)
    cmd_scope_show(_args(sf, name="prod"))
    out = capsys.readouterr().out
    assert "prod" in out


def test_cmd_scope_show_missing_scope(sf, capsys):
    cmd_scope_show(_args(sf, name="ghost"))
    out = capsys.readouterr().out
    assert "not found" in out


def test_cmd_scope_list_shows_scopes(sf, capsys):
    save_scope(create_scope("alpha"), sf)
    save_scope(create_scope("beta"), sf)
    cmd_scope_list(_args(sf))
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_cmd_scope_list_empty(sf, capsys):
    cmd_scope_list(_args(sf))
    out = capsys.readouterr().out
    assert "No scopes" in out


def test_cmd_scope_delete_removes(sf, capsys):
    save_scope(create_scope("temp"), sf)
    cmd_scope_delete(_args(sf, name="temp"))
    assert load_scope("temp", sf) is None


def test_cmd_scope_delete_missing_prints_not_found(sf, capsys):
    cmd_scope_delete(_args(sf, name="ghost"))
    out = capsys.readouterr().out
    assert "not found" in out
