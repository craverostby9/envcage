"""Tests for envcage.env_format."""
from __future__ import annotations

import json
import os
import pytest

from envcage.env_format import (
    FormatIssue,
    FormatReport,
    check_snapshot,
    check_snapshot_file,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
clean_env():
    return {
        "APP_NAME": "myapp",
        "PORT": "8080",
        "DB_HOST": "localhost",
    }


@pytest.fixture()
def messy_env():
    return {
        "app_name": "myapp",          # lowercase key
        "1INVALID": "bad",            # key starts with digit
        "SPACED": "  hello  ",        # leading/trailing whitespace in value
        "CTRL": "val\x01ue",          # control char in value
        "GOOD_KEY": "good",
    }


@pytest.fixture()
def snap_file(tmp_path, clean_env):
    path = tmp_path / "snap.json"
    payload = {"env": clean_env, "required": list(clean_env.keys())}
    path.write_text(json.dumps(payload))
    return str(path)


# ---------------------------------------------------------------------------
# check_snapshot — clean env
# ---------------------------------------------------------------------------

def test_clean_env_has_no_issues(clean_env):
    report = check_snapshot(clean_env)
    assert not report.any_issues


def test_clean_env_issue_count_zero(clean_env):
    report = check_snapshot(clean_env)
    assert report.issue_count == 0


def test_clean_env_summary_no_issues(clean_env):
    report = check_snapshot(clean_env)
    assert "No formatting issues" in report.summary()


# ---------------------------------------------------------------------------
# check_snapshot — messy env
# ---------------------------------------------------------------------------

def test_messy_env_detects_lowercase_key(messy_env):
    report = check_snapshot(messy_env)
    kinds = [i.kind for i in report.issues]
    assert "key_case" in kinds


def test_messy_env_detects_invalid_key_chars(messy_env):
    report = check_snapshot(messy_env)
    kinds = [i.kind for i in report.issues]
    assert "key_chars" in kinds


def test_messy_env_detects_value_whitespace(messy_env):
    report = check_snapshot(messy_env)
    kinds = [i.kind for i in report.issues]
    assert "value_whitespace" in kinds


def test_messy_env_detects_control_chars(messy_env):
    report = check_snapshot(messy_env)
    kinds = [i.kind for i in report.issues]
    assert "value_control" in kinds


def test_messy_env_any_issues_true(messy_env):
    report = check_snapshot(messy_env)
    assert report.any_issues


def test_messy_env_summary_contains_count(messy_env):
    report = check_snapshot(messy_env)
    assert str(report.issue_count) in report.summary()


def test_by_kind_filters_correctly(messy_env):
    report = check_snapshot(messy_env)
    whitespace_issues = report.by_kind("value_whitespace")
    assert all(i.kind == "value_whitespace" for i in whitespace_issues)


def test_good_key_in_messy_env_not_flagged(messy_env):
    report = check_snapshot(messy_env)
    flagged_keys = {i.key for i in report.issues}
    assert "GOOD_KEY" not in flagged_keys


# ---------------------------------------------------------------------------
# FormatIssue.to_dict
# ---------------------------------------------------------------------------

def test_format_issue_to_dict():
    issue = FormatIssue(key="bad_key", kind="key_case", message="lowercase")
    d = issue.to_dict()
    assert d["key"] == "bad_key"
    assert d["kind"] == "key_case"
    assert d["message"] == "lowercase"


# ---------------------------------------------------------------------------
# check_snapshot_file
# ---------------------------------------------------------------------------

def test_check_snapshot_file_clean(snap_file):
    report = check_snapshot_file(snap_file)
    assert not report.any_issues
