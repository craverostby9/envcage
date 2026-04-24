"""Tests for env_snapshot_compare_report module."""
import json
from pathlib import Path

import pytest

from envcage.env_snapshot_compare_report import (
    CompareReportEntry,
    MultiCompareReport,
    build_multi_compare_report,
    build_multi_compare_report_from_files,
    save_report,
)
from envcage.snapshot import save


@pytest.fixture
def three_snaps():
    return {
        "prod": {"env": {"DB_HOST": "prod-db", "APP_ENV": "production", "PORT": "5432"}},
        "staging": {"env": {"DB_HOST": "staging-db", "APP_ENV": "staging", "PORT": "5432"}},
        "dev": {"env": {"DB_HOST": "localhost", "APP_ENV": "development", "PORT": "5432"}},
    }


@pytest.fixture
def identical_snaps():
    return {
        "a": {"env": {"KEY": "value", "OTHER": "same"}},
        "b": {"env": {"KEY": "value", "OTHER": "same"}},
    }


def test_build_report_returns_multi_compare_report(three_snaps):
    report = build_multi_compare_report(three_snaps)
    assert isinstance(report, MultiCompareReport)


def test_build_report_snapshot_names_preserved(three_snaps):
    report = build_multi_compare_report(three_snaps)
    assert set(report.snapshot_names) == {"prod", "staging", "dev"}


def test_build_report_entries_cover_all_keys(three_snaps):
    report = build_multi_compare_report(three_snaps)
    keys = {e.key for e in report.entries}
    assert keys == {"DB_HOST", "APP_ENV", "PORT"}


def test_port_is_consistent_across_all(three_snaps):
    report = build_multi_compare_report(three_snaps)
    port_entry = next(e for e in report.entries if e.key == "PORT")
    assert port_entry.consistent is True


def test_db_host_is_inconsistent(three_snaps):
    report = build_multi_compare_report(three_snaps)
    db_entry = next(e for e in report.entries if e.key == "DB_HOST")
    assert db_entry.consistent is False


def test_any_inconsistencies_true_when_diffs_exist(three_snaps):
    report = build_multi_compare_report(three_snaps)
    assert report.any_inconsistencies is True


def test_any_inconsistencies_false_for_identical(identical_snaps):
    report = build_multi_compare_report(identical_snaps)
    assert report.any_inconsistencies is False


def test_inconsistent_keys_lists_bad_keys(three_snaps):
    report = build_multi_compare_report(three_snaps)
    assert "DB_HOST" in report.inconsistent_keys
    assert "PORT" not in report.inconsistent_keys


def test_summary_all_consistent(identical_snaps):
    report = build_multi_compare_report(identical_snaps)
    s = report.summary()
    assert "consistent" in s
    assert "2" in s  # 2 keys


def test_summary_shows_inconsistent_count(three_snaps):
    report = build_multi_compare_report(three_snaps)
    s = report.summary()
    assert "inconsistent" in s


def test_to_dict_contains_expected_keys(three_snaps):
    report = build_multi_compare_report(three_snaps)
    d = report.to_dict()
    assert "snapshot_names" in d
    assert "entries" in d
    assert "any_inconsistencies" in d
    assert "summary" in d


def test_entry_values_map_snapshot_to_value(three_snaps):
    report = build_multi_compare_report(three_snaps)
    port_entry = next(e for e in report.entries if e.key == "PORT")
    assert port_entry.values["prod"] == "5432"
    assert port_entry.values["dev"] == "5432"


def test_missing_key_in_one_snapshot_is_inconsistent(tmp_path):
    snaps = {
        "a": {"env": {"ONLY_A": "yes", "SHARED": "x"}},
        "b": {"env": {"SHARED": "x"}},
    }
    report = build_multi_compare_report(snaps)
    only_a = next(e for e in report.entries if e.key == "ONLY_A")
    assert only_a.consistent is False
    assert only_a.values["b"] is None


def test_build_from_files(tmp_path):
    snap_a = tmp_path / "snap_a.json"
    snap_b = tmp_path / "snap_b.json"
    save({"env": {"KEY": "val1"}}, str(snap_a))
    save({"env": {"KEY": "val2"}}, str(snap_b))
    report = build_multi_compare_report_from_files([str(snap_a), str(snap_b)])
    assert len(report.entries) == 1
    assert report.entries[0].key == "KEY"
    assert report.any_inconsistencies is True


def test_save_report_writes_valid_json(tmp_path, three_snaps):
    report = build_multi_compare_report(three_snaps)
    out = tmp_path / "report.json"
    save_report(report, str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert "entries" in data
