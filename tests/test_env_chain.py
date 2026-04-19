"""Tests for envcage.env_chain."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.env_chain import (
    create_chain,
    load_chain,
    resolve,
    resolve_key,
    save_chain,
    source_of,
)


# ---------- helpers ----------

def _write_snap(path: Path, env: dict) -> str:
    data = {"name": path.stem, "env": env, "required": []}
    path.write_text(json.dumps(data))
    return str(path)


# ---------- fixtures ----------

@pytest.fixture()
def snap_files(tmp_path):
    base = _write_snap(tmp_path / "base.json", {"APP": "base", "DB": "base_db"})
    override = _write_snap(tmp_path / "override.json", {"APP": "override", "EXTRA": "yes"})
    return base, override


# ---------- create / persist ----------

def test_create_chain_stores_name():
    c = create_chain("mychain")
    assert c.name == "mychain"


def test_create_chain_stores_description():
    c = create_chain("c", description="test chain")
    assert c.description == "test chain"


def test_create_chain_stores_snapshots(snap_files):
    base, override = snap_files
    c = create_chain("c", snapshots=[base, override])
    assert c.snapshots == [base, override]


def test_create_chain_empty_snapshots_by_default():
    c = create_chain("c")
    assert c.snapshots == []


def test_save_creates_file(tmp_path, snap_files):
    c = create_chain("c", snapshots=list(snap_files))
    out = str(tmp_path / "chain.json")
    save_chain(c, out)
    assert Path(out).exists()


def test_save_file_is_valid_json(tmp_path):
    c = create_chain("c")
    out = str(tmp_path / "chain.json")
    save_chain(c, out)
    data = json.loads(Path(out).read_text())
    assert "name" in data and "snapshots" in data


def test_load_round_trips(tmp_path, snap_files):
    base, override = snap_files
    c = create_chain("round", snapshots=[base, override], description="d")
    out = str(tmp_path / "chain.json")
    save_chain(c, out)
    loaded = load_chain(out)
    assert loaded.name == "round"
    assert loaded.description == "d"
    assert loaded.snapshots == [base, override]


def test_load_chain_missing_file_raises(tmp_path):
    """load_chain should raise an informative error for a missing file."""
    missing = str(tmp_path / "nonexistent.json")
    with pytest.raises((FileNotFoundError, OSError)):
        load_chain(missing)


# ---------- resolution ----------

def test_resolve_merges_all_keys(snap_files):
    base, override = snap_files
    c = create_chain("c", snapshots=[override, base])  # override has priority
    merged = resolve(c)
    assert "APP" in merged
    assert "DB" in merged
    assert "EXTRA" in merged


def test_resolve_first_snapshot_wins(snap_files):
    base, override = snap_files
    # override listed first → highest priority
    c = create_chain("c", snapshots=[override, base])
    assert resolve(c)["APP"] == "override"


def test_resolve_fallback_to_lower_priority(snap_files):
    base, override = snap_files
    c = create_chain("c", snapshots=[override, base])
    # DB only exists in base
    assert resolve(c)["DB"] == "base_db"


def test_resolve_key_returns_value(snap_files):
    base, override = snap_files
    c = create_chain("c", snapshots=[override, base])
    assert resolve
