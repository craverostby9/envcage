"""Tests for envcage.lint."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from envcage.lint import (
    LintIssue,
    LintReport,
    lint_snapshot,
    lint_snapshot_file,
    summary,
)


@pytest.fixture
def clean_env():
    return {'DATABASE_URL': 'postgres://localhost/db', 'API_KEY': 'abc123'}


@pytest.fixture
def messy_env():
    return {
        'database-url': 'postgres://localhost/db',  # bad case
        'EMPTY_VAL': '',                              # empty value
        'GOOD_KEY': 'value',
    }


def test_clean_env_passes(clean_env):
    report = lint_snapshot(clean_env)
    assert report.passed
    assert report.issues == []


def test_bad_key_name_raises_warning(messy_env):
    report = lint_snapshot(messy_env)
    keys_with_issues = {i.key for i in report.warnings}
    assert 'database-url' in keys_with_issues


def test_empty_value_raises_warning(messy_env):
    report = lint_snapshot(messy_env)
    keys_with_issues = {i.key for i in report.warnings}
    assert 'EMPTY_VAL' in keys_with_issues


def test_allow_empty_suppresses_empty_warning():
    env = {'MY_KEY': ''}
    report = lint_snapshot(env, allow_empty=True)
    empty_warnings = [i for i in report.warnings if 'empty' in i.message.lower()]
    assert empty_warnings == []


def test_value_too_long_is_error():
    env = {'LONG_KEY': 'x' * 2000}
    report = lint_snapshot(env, max_length=512)
    assert not report.passed
    assert any(i.key == 'LONG_KEY' and i.severity == 'error' for i in report.issues)


def test_require_screaming_snake_false_ignores_case():
    env = {'my-key': 'value', 'another.key': 'v'}
    report = lint_snapshot(env, require_screaming_snake=False)
    case_warnings = [
        i for i in report.warnings if 'SCREAMING_SNAKE' in i.message
    ]
    assert case_warnings == []


def test_passed_property_false_when_errors_present():
    env = {'BIG': 'z' * 2000}
    report = lint_snapshot(env, max_length=100)
    assert not report.passed


def test_summary_no_issues(clean_env):
    report = lint_snapshot(clean_env)
    assert 'No lint issues found' in summary(report)


def test_summary_includes_counts(messy_env):
    report = lint_snapshot(messy_env)
    s = summary(report)
    assert 'error(s)' in s
    assert 'warning(s)' in s


def test_lint_snapshot_file(tmp_path, clean_env):
    snap_file = tmp_path / 'snap.json'
    snap_file.write_text(json.dumps({'env': clean_env, 'meta': {}}))
    report = lint_snapshot_file(str(snap_file))
    assert report.passed


def test_lint_snapshot_file_detects_issues(tmp_path):
    bad_env = {'bad-key': '', 'GOOD': 'ok'}
    snap_file = tmp_path / 'snap.json'
    snap_file.write_text(json.dumps({'env': bad_env, 'meta': {}}))
    report = lint_snapshot_file(str(snap_file))
    assert len(report.warnings) >= 2


def test_lint_issue_str():
    issue = LintIssue(key='FOO', severity='warning', message='Something odd.')
    assert '[WARNING]' in str(issue)
    assert 'FOO' in str(issue)
