"""Tests for envcage.template."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.template import (
    apply_template,
    create_template,
    load_template,
    missing_keys,
    save_template,
    template_from_snapshot,
)


# ---------------------------------------------------------------------------
# create_template
# ---------------------------------------------------------------------------

def test_create_template_stores_sorted_unique_keys():
    tmpl = create_template(["Z_KEY", "A_KEY", "A_KEY"])
    assert tmpl["keys"] == ["A_KEY", "Z_KEY"]


def test_create_template_stores_description():
    tmpl = create_template(["FOO"], description="prod template")
    assert tmpl["description"] == "prod template"


def test_create_template_empty_keys():
    tmpl = create_template([])
    assert tmpl["keys"] == []


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    tmpl = create_template(["DB_URL", "SECRET_KEY"])
    dest = tmp_path / "tmpl.json"
    save_template(tmpl, dest)
    assert dest.exists()


def test_save_file_is_valid_json(tmp_path):
    tmpl = create_template(["DB_URL"])
    dest = tmp_path / "tmpl.json"
    save_template(tmpl, dest)
    data = json.loads(dest.read_text())
    assert "keys" in data


def test_load_returns_original_template(tmp_path):
    tmpl = create_template(["DB_URL", "SECRET_KEY"], description="test")
    dest = tmp_path / "tmpl.json"
    save_template(tmpl, dest)
    loaded = load_template(dest)
    assert loaded == tmpl


def test_save_creates_parent_dirs(tmp_path):
    dest = tmp_path / "nested" / "dir" / "tmpl.json"
    save_template(create_template(["X"]), dest)
    assert dest.exists()


# ---------------------------------------------------------------------------
# template_from_snapshot
# ---------------------------------------------------------------------------

def test_template_from_snapshot_extracts_keys():
    snap = {"env": {"DB_URL": "postgres://", "PORT": "5432"}}
    tmpl = template_from_snapshot(snap)
    assert set(tmpl["keys"]) == {"DB_URL", "PORT"}


def test_template_from_snapshot_description():
    snap = {"env": {"FOO": "bar"}}
    tmpl = template_from_snapshot(snap, description="from prod")
    assert tmpl["description"] == "from prod"


# ---------------------------------------------------------------------------
# apply_template
# ---------------------------------------------------------------------------

def test_apply_template_fills_provided_values():
    tmpl = create_template(["A", "B", "C"])
    result = apply_template(tmpl, {"A": "1", "C": "3"})
    assert result["A"] == "1"
    assert result["C"] == "3"


def test_apply_template_defaults_missing_to_empty_string():
    tmpl = create_template(["A", "B"])
    result = apply_template(tmpl, {"A": "hello"})
    assert result["B"] == ""


# ---------------------------------------------------------------------------
# missing_keys
# ---------------------------------------------------------------------------

def test_missing_keys_detects_absent_keys():
    tmpl = create_template(["A", "B", "C"])
    snap = {"env": {"A": "1"}}
    assert set(missing_keys(tmpl, snap)) == {"B", "C"}


def test_missing_keys_empty_when_all_present():
    tmpl = create_template(["A", "B"])
    snap = {"env": {"A": "1", "B": "2"}}
    assert missing_keys(tmpl, snap) == []


def test_missing_keys_empty_template():
    tmpl = create_template([])
    snap = {"env": {"A": "1"}}
    assert missing_keys(tmpl, snap) == []
