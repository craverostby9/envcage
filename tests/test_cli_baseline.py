"""Tests for envcage.cli_baseline."""

from __future__ import annotations

import argparse
import pytest

from envcage.snapshot import save
from envcage import cli_baseline
from envcage.baseline import set_baseline, get_baseline


def _args(**kwargs):
    ns = argparse.Namespace()
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


@pytest.fixture(autouse=True)
def _patch_baseline_file(tmp_path, monkeypatch):
    bf = str(tmp_path / "baselines.json")
    monkeypatch.setattr(cli_baseline, "_BASELINE_FILE", bf)
    return bf


@pytest.fixture()
def snap_file(tmp_path):
    path = str(tmp_path / "snap.json")
    save({"env": {"X": "1"}, "required": []}, path)
    return path


def test_cmd_baseline_set_prints_confirmation(snap_file, capsys):
    cli_baseline.cmd_baseline_set(_args(label="prod", snapshot=snap_file))
    out = capsys.readouterr().out
    assert "prod" in out
    assert snap_file in out


def test_cmd_baseline_set_persists(snap_file, _patch_baseline_file):
    cli_baseline.cmd_baseline_set(_args(label="prod", snapshot=snap_file))
    assert get_baseline("prod", _patch_baseline_file) == snap_file


def test_cmd_baseline_remove_existing(snap_file, capsys):
    cli_baseline.cmd_baseline_set(_args(label="staging", snapshot=snap_file))
    cli_baseline.cmd_baseline_remove(_args(label="staging"))
    out = capsys.readouterr().out
    assert "Removed" in out


def test_cmd_baseline_remove_missing(capsys):
    cli_baseline.cmd_baseline_remove(_args(label="ghost"))
    out = capsys.readouterr().out
    assert "No baseline" in out


def test_cmd_baseline_list_empty(capsys):
    cli_baseline.cmd_baseline_list(_args())
    out = capsys.readouterr().out
    assert "No baselines" in out


def test_cmd_baseline_list_shows_entries(snap_file, capsys):
    cli_baseline.cmd_baseline_set(_args(label="alpha", snapshot=snap_file))
    cli_baseline.cmd_baseline_list(_args())
    out = capsys.readouterr().out
    assert "alpha" in out


def test_cmd_baseline_drift_no_drift(snap_file, monkeypatch, capsys):
    cli_baseline.cmd_baseline_set(_args(label="prod", snapshot=snap_file))
    monkeypatch.setattr(
        cli_baseline,
        "capture",
        lambda **kw: {"env": {"X": "1"}, "required": []},
    )
    cli_baseline.cmd_baseline_drift(_args(label="prod"))
    out = capsys.readouterr().out
    assert "No drift" in out


def test_cmd_baseline_drift_shows_changes(snap_file, monkeypatch, capsys):
    cli_baseline.cmd_baseline_set(_args(label="prod", snapshot=snap_file))
    monkeypatch.setattr(
        cli_baseline,
        "capture",
        lambda **kw: {"env": {"X": "1", "NEW": "yes"}, "required": []},
    )
    cli_baseline.cmd_baseline_drift(_args(label="prod"))
    out = capsys.readouterr().out
    assert "NEW" in out or "drift" in out.lower()
