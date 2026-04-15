"""Tests for envcage.cli_alias."""
import argparse
import pytest

from envcage.cli_alias import (
    cmd_alias_set,
    cmd_alias_remove,
    cmd_alias_resolve,
    cmd_alias_list,
    cmd_alias_find,
)
from envcage.env_alias import set_alias, resolve_alias


def _args(**kwargs) -> argparse.Namespace:
    defaults = {"alias_file": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def af(tmp_path) -> str:
    return str(tmp_path / "aliases.json")


def test_cmd_alias_set_persists(af, capsys):
    cmd_alias_set(_args(name="prod", snapshot="prod.json", alias_file=af))
    assert resolve_alias("prod", af) == "prod.json"


def test_cmd_alias_set_prints_confirmation(af, capsys):
    cmd_alias_set(_args(name="prod", snapshot="prod.json", alias_file=af))
    out = capsys.readouterr().out
    assert "prod" in out
    assert "prod.json" in out


def test_cmd_alias_remove_removes(af, capsys):
    set_alias("staging", "staging.json", af)
    cmd_alias_remove(_args(name="staging", alias_file=af))
    assert resolve_alias("staging", af) is None


def test_cmd_alias_remove_missing_exits_one(af):
    with pytest.raises(SystemExit) as exc:
        cmd_alias_remove(_args(name="ghost", alias_file=af))
    assert exc.value.code == 1


def test_cmd_alias_resolve_prints_path(af, capsys):
    set_alias("dev", "dev.json", af)
    cmd_alias_resolve(_args(name="dev", alias_file=af))
    out = capsys.readouterr().out
    assert "dev.json" in out


def test_cmd_alias_resolve_missing_exits_one(af):
    with pytest.raises(SystemExit) as exc:
        cmd_alias_resolve(_args(name="nope", alias_file=af))
    assert exc.value.code == 1


def test_cmd_alias_list_shows_all(af, capsys):
    set_alias("prod", "prod.json", af)
    set_alias("dev", "dev.json", af)
    cmd_alias_list(_args(alias_file=af))
    out = capsys.readouterr().out
    assert "prod" in out
    assert "dev" in out


def test_cmd_alias_list_empty_message(af, capsys):
    cmd_alias_list(_args(alias_file=af))
    out = capsys.readouterr().out
    assert "No aliases" in out


def test_cmd_alias_find_shows_names(af, capsys):
    set_alias("prod", "shared.json", af)
    set_alias("live", "shared.json", af)
    cmd_alias_find(_args(snapshot="shared.json", alias_file=af))
    out = capsys.readouterr().out
    assert "prod" in out
    assert "live" in out


def test_cmd_alias_find_no_match_message(af, capsys):
    cmd_alias_find(_args(snapshot="unknown.json", alias_file=af))
    out = capsys.readouterr().out
    assert "No aliases" in out
