"""Tests for envcage.validate module."""

import json
import os
import tempfile

import pytest

from envcage.validate import ValidationResult, validate_snapshot, validate_snapshot_file


SAMPLE_SNAPSHOT = {
    "meta": {"name": "test", "timestamp": "2024-01-01T00:00:00"},
    "env": {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123", "DEBUG": "false"},
}


@pytest.fixture
def snapshot():
    return {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123", "DEBUG": "false"}


def test_valid_snapshot_passes(snapshot):
    result = validate_snapshot(snapshot, required_keys=["DATABASE_URL", "SECRET_KEY"])
    assert result.is_valid


def test_missing_keys_detected(snapshot):
    result = validate_snapshot(snapshot, required_keys=["DATABASE_URL", "MISSING_KEY"])
    assert not result.is_valid
    assert "MISSING_KEY" in result.missing


def test_no_false_missing_keys(snapshot):
    result = validate_snapshot(snapshot, required_keys=["DATABASE_URL"])
    assert result.missing == []


def test_extra_keys_ignored_by_default(snapshot):
    result = validate_snapshot(snapshot, required_keys=["DATABASE_URL"])
    assert result.extra == []


def test_extra_keys_reported_when_disallowed(snapshot):
    result = validate_snapshot(snapshot, required_keys=["DATABASE_URL"], allowed_extra=False)
    assert "SECRET_KEY" in result.extra
    assert "DEBUG" in result.extra


def test_rule_passes_for_valid_value(snapshot):
    rules = {"DEBUG": lambda v: None if v in ("true", "false") else "must be 'true' or 'false'"}
    result = validate_snapshot(snapshot, required_keys=[], rules=rules)
    assert result.is_valid
    assert "DEBUG" not in result.invalid


def test_rule_fails_for_invalid_value(snapshot):
    rules = {"DEBUG": lambda v: None if v in ("true", "false") else "must be 'true' or 'false'"}
    snapshot["DEBUG"] = "yes"
    result = validate_snapshot(snapshot, required_keys=[], rules=rules)
    assert not result.is_valid
    assert "DEBUG" in result.invalid


def test_rule_skipped_for_missing_key(snapshot):
    rules = {"NONEXISTENT": lambda v: "always fails"}
    result = validate_snapshot(snapshot, required_keys=[], rules=rules)
    assert result.is_valid


def test_summary_all_passed(snapshot):
    result = validate_snapshot(snapshot, required_keys=["DATABASE_URL"])
    assert result.summary() == "All checks passed."


def test_summary_includes_missing(snapshot):
    result = validate_snapshot(snapshot, required_keys=["MISSING_KEY"])
    assert "Missing keys" in result.summary()
    assert "MISSING_KEY" in result.summary()


def test_validate_snapshot_file(tmp_path):
    snapshot_path = tmp_path / "snap.json"
    snapshot_path.write_text(json.dumps(SAMPLE_SNAPSHOT))
    result = validate_snapshot_file(str(snapshot_path), required_keys=["DATABASE_URL", "SECRET_KEY"])
    assert result.is_valid


def test_validate_snapshot_file_missing_key(tmp_path):
    snapshot_path = tmp_path / "snap.json"
    snapshot_path.write_text(json.dumps(SAMPLE_SNAPSHOT))
    result = validate_snapshot_file(str(snapshot_path), required_keys=["MISSING_KEY"])
    assert not result.is_valid
    assert "MISSING_KEY" in result.missing
