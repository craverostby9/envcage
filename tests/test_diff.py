"""Tests for envcage.diff module."""

import json
import os
import tempfile

import pytest

from envcage.diff import DiffResult, diff_snapshot_files, diff_snapshots


OLD_ENV = {"APP_ENV": "staging", "DB_HOST": "localhost", "SECRET": "old_secret"}
NEW_ENV = {"APP_ENV": "production", "DB_HOST": "localhost", "NEW_KEY": "hello"}


def test_diff_detects_added_keys():
    result = diff_snapshots(OLD_ENV, NEW_ENV)
    assert "NEW_KEY" in result.added
    assert result.added["NEW_KEY"] == "hello"


def test_diff_detects_removed_keys():
    result = diff_snapshots(OLD_ENV, NEW_ENV)
    assert "SECRET" in result.removed
    assert result.removed["SECRET"] == "old_secret"


def test_diff_detects_changed_keys():
    result = diff_snapshots(OLD_ENV, NEW_ENV)
    assert "APP_ENV" in result.changed
    assert result.changed["APP_ENV"] == ("staging", "production")


def test_diff_unchanged_keys_not_reported():
    result = diff_snapshots(OLD_ENV, NEW_ENV)
    assert "DB_HOST" not in result.added
    assert "DB_HOST" not in result.removed
    assert "DB_HOST" not in result.changed


def test_diff_identical_envs_has_no_changes():
    result = diff_snapshots(OLD_ENV, OLD_ENV)
    assert not result.has_changes


def test_diff_restricted_to_keys():
    result = diff_snapshots(OLD_ENV, NEW_ENV, keys=["APP_ENV"])
    assert "APP_ENV" in result.changed
    assert "SECRET" not in result.removed
    assert "NEW_KEY" not in result.added


def test_summary_contains_added_prefix():
    result = diff_snapshots(OLD_ENV, NEW_ENV)
    summary = result.summary()
    assert "+ NEW_KEY" in summary


def test_summary_contains_removed_prefix():
    result = diff_snapshots(OLD_ENV, NEW_ENV)
    summary = result.summary()
    assert "- SECRET" in summary


def test_summary_contains_changed_prefix():
    result = diff_snapshots(OLD_ENV, NEW_ENV)
    summary = result.summary()
    assert "~ APP_ENV" in summary


def test_summary_no_differences_message():
    result = diff_snapshots(OLD_ENV, OLD_ENV)
    assert result.summary() == "No differences found."


def test_diff_snapshot_files(tmp_path):
    old_file = tmp_path / "old.json"
    new_file = tmp_path / "new.json"
    old_file.write_text(json.dumps(OLD_ENV))
    new_file.write_text(json.dumps(NEW_ENV))

    result = diff_snapshot_files(str(old_file), str(new_file))
    assert result.has_changes
    assert "NEW_KEY" in result.added
    assert "SECRET" in result.removed
    assert "APP_ENV" in result.changed
