"""Tests for envcage.cli_lint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from envcage.cli_lint import cmd_lint, register


def _args(**kwargs) -> argparse.Namespace:
    defaults = {
        'snapshots': [],
        'allow_empty': False,
        'max_length': 1024,
        'no_screaming_snake': False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture
def good_snap(tmp_path) -> Path:
    f = tmp_path / 'good.json'
    f.write_text(json.dumps({'env': {'DATABASE_URL': 'postgres://x'}, 'meta': {}}))
    return f


@pytest.fixture
def bad_snap(tmp_path) -> Path:
    f = tmp_path / 'bad.json'
    f.write_text(json.dumps({'env': {'bad-key': '', 'GOOD': 'ok'}, 'meta': {}}))
    return f


def test_cmd_lint_clean_file_exits_zero(good_snap, capsys):
    args = _args(snapshots=[str(good_snap)])
    cmd_lint(args)  # should not raise SystemExit


def test_cmd_lint_bad_file_exits_one(bad_snap):
    args = _args(snapshots=[str(bad_snap)])
    with pytest.raises(SystemExit) as exc_info:
        cmd_lint(args)
    assert exc_info.value.code == 1


def test_cmd_lint_prints_path_header(good_snap, capsys):
    args = _args(snapshots=[str(good_snap)])
    cmd_lint(args)
    captured = capsys.readouterr()
    assert str(good_snap) in captured.out


def test_cmd_lint_prints_no_issues_message(good_snap, capsys):
    args = _args(snapshots=[str(good_snap)])
    cmd_lint(args)
    captured = capsys.readouterr()
    assert 'No lint issues found' in captured.out


def test_cmd_lint_multiple_files_one_bad(good_snap, bad_snap):
    args = _args(snapshots=[str(good_snap), str(bad_snap)])
    with pytest.raises(SystemExit) as exc_info:
        cmd_lint(args)
    assert exc_info.value.code == 1


def test_cmd_lint_allow_empty_suppresses_warning(tmp_path, capsys):
    f = tmp_path / 'empty.json'
    f.write_text(json.dumps({'env': {'MY_VAR': ''}, 'meta': {}}))
    args = _args(snapshots=[str(f)], allow_empty=True)
    cmd_lint(args)  # should not raise
    captured = capsys.readouterr()
    assert 'No lint issues found' in captured.out


def test_register_adds_lint_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    register(subparsers)
    parsed = parser.parse_args(['lint', 'snap.json'])
    assert parsed.snapshots == ['snap.json']
    assert hasattr(parsed, 'func')
