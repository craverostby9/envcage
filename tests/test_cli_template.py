"""Tests for envcage.cli_template."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from envcage import template as tmpl_mod
from envcage.cli_template import (
    cmd_template_check,
    cmd_template_create,
    cmd_template_from_snapshot,
    cmd_template_scaffold,
    cmd_template_show,
)
from envcage.snapshot import save as save_snapshot


def _args(**kwargs):
    ns = types.SimpleNamespace(description="", **kwargs)
    return ns


# ---------------------------------------------------------------------------
# cmd_template_create
# ---------------------------------------------------------------------------

def test_cmd_template_create_writes_file(tmp_path):
    dest = tmp_path / "tmpl.json"
    rc = cmd_template_create(_args(keys=["A", "B"], output=str(dest)))
    assert rc == 0
    assert dest.exists()


def test_cmd_template_create_keys_persisted(tmp_path):
    dest = tmp_path / "tmpl.json"
    cmd_template_create(_args(keys=["FOO", "BAR"], output=str(dest)))
    tmpl = tmpl_mod.load_template(dest)
    assert set(tmpl["keys"]) == {"FOO", "BAR"}


# ---------------------------------------------------------------------------
# cmd_template_from_snapshot
# ---------------------------------------------------------------------------

def test_cmd_template_from_snapshot_derives_keys(tmp_path):
    snap_path = tmp_path / "snap.json"
    save_snapshot({"env": {"DB_URL": "x", "PORT": "5432"}}, str(snap_path))
    dest = tmp_path / "tmpl.json"
    rc = cmd_template_from_snapshot(_args(snapshot=str(snap_path), output=str(dest)))
    assert rc == 0
    tmpl = tmpl_mod.load_template(dest)
    assert set(tmpl["keys"]) == {"DB_URL", "PORT"}


# ---------------------------------------------------------------------------
# cmd_template_check
# ---------------------------------------------------------------------------

def test_cmd_template_check_passes_when_all_keys_present(tmp_path):
    tmpl_path = tmp_path / "tmpl.json"
    snap_path = tmp_path / "snap.json"
    tmpl_mod.save_template(tmpl_mod.create_template(["A", "B"]), tmpl_path)
    save_snapshot({"env": {"A": "1", "B": "2"}}, str(snap_path))
    rc = cmd_template_check(_args(template=str(tmpl_path), snapshot=str(snap_path)))
    assert rc == 0


def test_cmd_template_check_fails_when_keys_missing(tmp_path):
    tmpl_path = tmp_path / "tmpl.json"
    snap_path = tmp_path / "snap.json"
    tmpl_mod.save_template(tmpl_mod.create_template(["A", "B", "C"]), tmpl_path)
    save_snapshot({"env": {"A": "1"}}, str(snap_path))
    rc = cmd_template_check(_args(template=str(tmpl_path), snapshot=str(snap_path)))
    assert rc == 1


# ---------------------------------------------------------------------------
# cmd_template_show
# ---------------------------------------------------------------------------

def test_cmd_template_show_returns_zero(tmp_path, capsys):
    tmpl_path = tmp_path / "tmpl.json"
    tmpl_mod.save_template(tmpl_mod.create_template(["X"], description="demo"), tmpl_path)
    rc = cmd_template_show(_args(template=str(tmpl_path)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "X" in out
    assert "demo" in out


# ---------------------------------------------------------------------------
# cmd_template_scaffold
# ---------------------------------------------------------------------------

def test_cmd_template_scaffold_writes_dotenv(tmp_path):
    tmpl_path = tmp_path / "tmpl.json"
    out_path = tmp_path / ".env.scaffold"
    tmpl_mod.save_template(tmpl_mod.create_template(["FOO", "BAR"]), tmpl_path)
    rc = cmd_template_scaffold(_args(template=str(tmpl_path), output=str(out_path)))
    assert rc == 0
    content = out_path.read_text()
    assert "FOO=" in content
    assert "BAR=" in content


def test_cmd_template_scaffold_stdout(tmp_path, capsys):
    tmpl_path = tmp_path / "tmpl.json"
    tmpl_mod.save_template(tmpl_mod.create_template(["KEY"]), tmpl_path)
    rc = cmd_template_scaffold(_args(template=str(tmpl_path), output="-"))
    assert rc == 0
    assert "KEY=" in capsys.readouterr().out
