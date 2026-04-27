"""Tests for envcage.env_snapshot_summary."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envcage.env_snapshot_summary import (
    SnapshotSummaryEntry,
    SnapshotSummaryReport,
    summarise_snapshot_file,
    build_report,
)


@pytest.fixture()
def snap_file(tmp_path: Path) -> str:
    data = {
        "env": {
            "APP_NAME": "myapp",
            "SECRET_KEY": "s3cr3t",
            "DATABASE_URL": "postgres://localhost/db",
            "EMPTY_VAR": "",
            "DUPLICATE_A": "same",
            "DUPLICATE_B": "same",
        }
    }
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(data))
    return str(p)


@pytest.fixture()
def snap_file2(tmp_path: Path) -> str:
    data = {"env": {"FOO": "bar", "BAZ": "qux"}}
    p = tmp_path / "snap2.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_summarise_returns_entry(snap_file):
    entry = summarise_snapshot_file(snap_file)
    assert isinstance(entry, SnapshotSummaryEntry)


def test_summarise_total_keys(snap_file):
    entry = summarise_snapshot_file(snap_file)
    assert entry.total_keys == 6


def test_summarise_sensitive_keys_detected(snap_file):
    entry = summarise_snapshot_file(snap_file)
    assert entry.sensitive_keys >= 1


def test_summarise_empty_values_counted(snap_file):
    entry = summarise_snapshot_file(snap_file)
    assert entry.empty_values == 1


def test_summarise_duplicate_values_counted(snap_file):
    entry = summarise_snapshot_file(snap_file)
    assert entry.duplicate_values >= 1


def test_summarise_name_is_stem(snap_file):
    entry = summarise_snapshot_file(snap_file)
    assert entry.name == "snap"


def test_summarise_tags_stored(snap_file):
    entry = summarise_snapshot_file(snap_file, tags=["prod", "v2"])
    assert entry.tags == ["prod", "v2"]


def test_summarise_note_stored(snap_file):
    entry = summarise_snapshot_file(snap_file, note="baseline release")
    assert entry.note == "baseline release"


def test_build_report_returns_report(snap_file, snap_file2):
    report = build_report([snap_file, snap_file2])
    assert isinstance(report, SnapshotSummaryReport)


def test_build_report_entry_count(snap_file, snap_file2):
    report = build_report([snap_file, snap_file2])
    assert report.total_snapshots == 2


def test_build_report_total_keys(snap_file, snap_file2):
    report = build_report([snap_file, snap_file2])
    assert report.total_keys == 8


def test_summary_string_contains_names(snap_file, snap_file2):
    report = build_report([snap_file, snap_file2])
    text = report.summary()
    assert "snap" in text
    assert "snap2" in text


def test_to_dict_round_trips(snap_file):
    entry = summarise_snapshot_file(snap_file, tags=["ci"], note="test")
    d = entry.to_dict()
    assert d["name"] == entry.name
    assert d["total_keys"] == entry.total_keys
    assert d["tags"] == ["ci"]
    assert d["note"] == "test"


def test_build_report_empty():
    report = build_report([])
    assert report.total_snapshots == 0
    assert report.total_keys == 0
