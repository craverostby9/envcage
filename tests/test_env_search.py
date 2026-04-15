"""Tests for envcage.env_search."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from envcage.env_search import (
    SearchMatch,
    SearchResult,
    search_snapshot,
    search_snapshot_files,
    summary,
)


@pytest.fixture
def simple_snap():
    return {
        "env": {
            "DATABASE_URL": "postgres://localhost/mydb",
            "SECRET_KEY": "s3cr3t",
            "APP_ENV": "production",
            "PORT": "8080",
        }
    }


@pytest.fixture
def snap_file(tmp_path, simple_snap):
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(simple_snap))
    return str(p)


def test_search_key_by_pattern(simple_snap):
    matches = search_snapshot(simple_snap, "DATABASE")
    assert len(matches) == 1
    assert matches[0].key == "DATABASE_URL"


def test_search_is_case_insensitive_by_default(simple_snap):
    matches = search_snapshot(simple_snap, "database_url")
    assert len(matches) == 1
    assert matches[0].key == "DATABASE_URL"


def test_search_case_sensitive_no_match(simple_snap):
    matches = search_snapshot(simple_snap, "database_url", case_sensitive=True)
    assert len(matches) == 0


def test_search_case_sensitive_match(simple_snap):
    matches = search_snapshot(simple_snap, "DATABASE_URL", case_sensitive=True)
    assert len(matches) == 1


def test_search_values_finds_match(simple_snap):
    matches = search_snapshot(simple_snap, "postgres", search_values=True)
    assert any(m.key == "DATABASE_URL" for m in matches)


def test_search_values_off_by_default(simple_snap):
    matches = search_snapshot(simple_snap, "postgres")
    assert len(matches) == 0


def test_search_multiple_keys_matched(simple_snap):
    matches = search_snapshot(simple_snap, "_")
    keys = [m.key for m in matches]
    assert "DATABASE_URL" in keys
    assert "SECRET_KEY" in keys
    assert "APP_ENV" in keys


def test_search_records_snapshot_path(simple_snap):
    matches = search_snapshot(simple_snap, "PORT", snapshot_path="/some/path.json")
    assert matches[0].snapshot_path == "/some/path.json"


def test_search_invalid_pattern_raises(simple_snap):
    with pytest.raises(ValueError, match="Invalid search pattern"):
        search_snapshot(simple_snap, "[invalid")


def test_search_snapshot_files_aggregates(tmp_path, simple_snap):
    snap2 = {"env": {"PORT": "9090", "REDIS_URL": "redis://localhost"}}
    f1 = tmp_path / "a.json"
    f2 = tmp_path / "b.json"
    f1.write_text(json.dumps(simple_snap))
    f2.write_text(json.dumps(snap2))

    result = search_snapshot_files([str(f1), str(f2)], "PORT")
    assert result.total == 2
    assert len(result.snapshots_matched()) == 2


def test_search_result_no_matches_summary():
    result = SearchResult()
    assert summary(result) == "No matches found."


def test_search_result_summary_contains_key(simple_snap, snap_file):
    result = search_snapshot_files([snap_file], "SECRET_KEY")
    out = summary(result)
    assert "SECRET_KEY" in out
    assert "1 match" in out


def test_match_to_dict():
    m = SearchMatch(snapshot_path="env.json", key="FOO", value="bar")
    d = m.to_dict()
    assert d == {"snapshot": "env.json", "key": "FOO", "value": "bar"}
