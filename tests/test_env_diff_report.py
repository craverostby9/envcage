"""Tests for envcage.env_diff_report."""

import json
import pytest
from pathlib import Path

from envcage.snapshot import save
from envcage.env_diff_report import (
    build_report,
    save_report,
    load_report,
    DiffReport,
    DiffReportEntry,
)


@pytest.fixture()
def snap_dir(tmp_path):
    envs = {
        "snap_a.json": {"APP": "1", "DB": "postgres", "SECRET": "abc"},
        "snap_b.json": {"APP": "2", "DB": "postgres", "NEW_KEY": "hello"},
        "snap_c.json": {"APP": "2", "DB": "postgres", "NEW_KEY": "hello"},
    }
    for name, env in envs.items():
        save({"env": env, "keys": list(env)}, str(tmp_path / name))
    return tmp_path


def _pairs(names):
    pairs = []
    for i in range(len(names) - 1):
        pairs.append({"source": names[i], "target": names[i + 1]})
    return pairs


def test_build_report_returns_diff_report(snap_dir):
    pairs = _pairs(["snap_a.json", "snap_b.json"])
    report = build_report(pairs, snap_dir=str(snap_dir))
    assert isinstance(report, DiffReport)


def test_build_report_entry_count_matches_pairs(snap_dir):
    pairs = _pairs(["snap_a.json", "snap_b.json", "snap_c.json"])
    report = build_report(pairs, snap_dir=str(snap_dir))
    assert len(report.entries) == 2


def test_build_report_detects_added_key(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    entry = report.entries[0]
    assert "NEW_KEY" in entry.result.added


def test_build_report_detects_removed_key(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    entry = report.entries[0]
    assert "SECRET" in entry.result.removed


def test_build_report_detects_changed_key(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    entry = report.entries[0]
    assert "APP" in entry.result.changed


def test_any_changes_true_when_diffs_exist(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    assert report.any_changes() is True


def test_any_changes_false_when_identical(snap_dir):
    pairs = [{"source": "snap_b.json", "target": "snap_c.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    assert report.any_changes() is False


def test_summary_contains_changed_label(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    s = report.summary()
    assert "CHANGED" in s


def test_summary_contains_identical_label(snap_dir):
    pairs = [{"source": "snap_b.json", "target": "snap_c.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    s = report.summary()
    assert "IDENTICAL" in s


def test_custom_label_used_in_entry(snap_dir):
    pairs = [{"label": "prod->staging", "source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    assert report.entries[0].label == "prod->staging"


def test_save_report_creates_file(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    out = str(snap_dir / "report.json")
    save_report(report, out)
    assert Path(out).exists()


def test_save_report_is_valid_json(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    out = str(snap_dir / "report.json")
    save_report(report, out)
    data = json.loads(Path(out).read_text())
    assert "entries" in data


def test_load_report_returns_dict(snap_dir):
    pairs = [{"source": "snap_a.json", "target": "snap_b.json"}]
    report = build_report(pairs, snap_dir=str(snap_dir))
    out = str(snap_dir / "report.json")
    save_report(report, out)
    loaded = load_report(out)
    assert isinstance(loaded, dict)
    assert len(loaded["entries"]) == 1
