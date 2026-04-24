"""Tests for envcage.env_placeholder."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.env_placeholder import (
    PlaceholderReport,
    find_placeholders,
    find_placeholders_in_file,
    is_placeholder,
)


# ---------------------------------------------------------------------------
# is_placeholder
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", [
    "${DATABASE_URL}",
    "{{API_KEY}}",
    "<SECRET_TOKEN>",
    "__REPLACE_ME__",
    "prefix-${VAR}-suffix",
])
def test_is_placeholder_returns_true_for_known_patterns(value):
    assert is_placeholder(value) is True


@pytest.mark.parametrize("value", [
    "postgres://localhost/db",
    "my_actual_secret_value",
    "",
    "123",
    "hello world",
])
def test_is_placeholder_returns_false_for_real_values(value):
    assert is_placeholder(value) is False


# ---------------------------------------------------------------------------
# find_placeholders
# ---------------------------------------------------------------------------

@pytest.fixture
def mixed_env():
    return {
        "DATABASE_URL": "${DATABASE_URL}",
        "API_KEY": "real-key-abc123",
        "TOKEN": "{{TOKEN}}",
        "HOST": "localhost",
        "SECRET": "<SECRET>",
        "NORMAL": "just a value",
        "PLACEHOLDER": "__REPLACE__",
    }


def test_find_placeholders_detects_all(mixed_env):
    report = find_placeholders(mixed_env)
    assert report.any_found
    assert report.total == 4


def test_find_placeholders_affected_keys(mixed_env):
    report = find_placeholders(mixed_env)
    keys = set(report.affected_keys())
    assert "DATABASE_URL" in keys
    assert "TOKEN" in keys
    assert "SECRET" in keys
    assert "PLACEHOLDER" in keys
    assert "API_KEY" not in keys


def test_find_placeholders_clean_env_returns_empty():
    env = {"HOST": "localhost", "PORT": "5432"}
    report = find_placeholders(env)
    assert not report.any_found
    assert report.total == 0


def test_find_placeholders_summary_no_issues():
    report = find_placeholders({"KEY": "value"})
    assert "No unresolved" in report.summary()


def test_find_placeholders_summary_lists_keys(mixed_env):
    report = find_placeholders(mixed_env)
    summary = report.summary()
    assert "DATABASE_URL" in summary
    assert "TOKEN" in summary


def test_find_placeholders_match_has_pattern(mixed_env):
    report = find_placeholders(mixed_env)
    for m in report.matches:
        assert m.pattern  # non-empty pattern string
        assert m.key
        assert m.value


# ---------------------------------------------------------------------------
# find_placeholders_in_file
# ---------------------------------------------------------------------------

def test_find_placeholders_in_file_detects_issues(tmp_path):
    snap = {"env": {"DB": "${DB_URL}", "HOST": "localhost"}}
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(snap))
    report = find_placeholders_in_file(p)
    assert report.any_found
    assert "DB" in report.affected_keys()


def test_find_placeholders_in_file_clean(tmp_path):
    snap = {"env": {"HOST": "localhost", "PORT": "5432"}}
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(snap))
    report = find_placeholders_in_file(p)
    assert not report.any_found
