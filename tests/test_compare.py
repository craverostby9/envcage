"""Tests for envcage.compare."""

import json
import pytest

from envcage.compare import (
    CompareReport,
    compare_snapshots,
    compare_snapshot_files,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def snap_a():
    return {"env": {"HOST": "localhost", "PORT": "8080", "DEBUG": "true"}}


@pytest.fixture
def snap_b():
    return {"env": {"HOST": "prod.example.com", "PORT": "443", "LOG_LEVEL": "warn"}}


@pytest.fixture
def snap_c():
    return {"env": {"HOST": "localhost", "PORT": "8080", "DEBUG": "true"}}


# ---------------------------------------------------------------------------
# compare_snapshots
# ---------------------------------------------------------------------------

def test_compare_all_keys_present(snap_a, snap_b):
    report = compare_snapshots([snap_a, snap_b], labels=["a", "b"])
    assert set(report.all_keys) == {"HOST", "PORT", "DEBUG", "LOG_LEVEL"}


def test_compare_matrix_values(snap_a, snap_b):
    report = compare_snapshots([snap_a, snap_b], labels=["a", "b"])
    assert report.matrix["HOST"]["a"] == "localhost"
    assert report.matrix["HOST"]["b"] == "prod.example.com"


def test_missing_key_is_none(snap_a, snap_b):
    report = compare_snapshots([snap_a, snap_b], labels=["a", "b"])
    assert report.matrix["DEBUG"]["b"] is None
    assert report.matrix["LOG_LEVEL"]["a"] is None


def test_inconsistent_keys_detected(snap_a, snap_b):
    report = compare_snapshots([snap_a, snap_b], labels=["a", "b"])
    assert "HOST" in report.inconsistent_keys()
    assert "PORT" in report.inconsistent_keys()


def test_consistent_key_not_in_inconsistent(snap_a, snap_c):
    """Two identical snapshots should have no inconsistent keys."""
    report = compare_snapshots([snap_a, snap_c], labels=["a", "c"])
    assert report.inconsistent_keys() == []


def test_missing_in_reports_absent_keys(snap_a, snap_b):
    report = compare_snapshots([snap_a, snap_b], labels=["a", "b"])
    assert "LOG_LEVEL" in report.missing_in("a")
    assert "DEBUG" in report.missing_in("b")


def test_labels_default_to_snap_n(snap_a, snap_b):
    report = compare_snapshots([snap_a, snap_b])
    assert report.labels == ["snap_0", "snap_1"]


def test_mismatched_labels_raises(snap_a, snap_b):
    with pytest.raises(ValueError):
        compare_snapshots([snap_a, snap_b], labels=["only_one"])


def test_empty_snapshot_list():
    report = compare_snapshots([])
    assert report.all_keys == []
    assert report.labels == []


# ---------------------------------------------------------------------------
# compare_snapshot_files
# ---------------------------------------------------------------------------

def test_compare_snapshot_files(tmp_path, snap_a, snap_b):
    file_a = tmp_path / "a.json"
    file_b = tmp_path / "b.json"
    file_a.write_text(json.dumps(snap_a))
    file_b.write_text(json.dumps(snap_b))

    report = compare_snapshot_files(
        [str(file_a), str(file_b)], labels=["a", "b"]
    )
    assert "HOST" in report.all_keys
    assert report.matrix["HOST"]["a"] == "localhost"


def test_compare_snapshot_files_uses_paths_as_default_labels(tmp_path, snap_a, snap_b):
    file_a = tmp_path / "a.json"
    file_b = tmp_path / "b.json"
    file_a.write_text(json.dumps(snap_a))
    file_b.write_text(json.dumps(snap_b))

    report = compare_snapshot_files([str(file_a), str(file_b)])
    assert str(file_a) in report.labels
    assert str(file_b) in report.labels
