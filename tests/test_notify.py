"""Tests for envcage.notify."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.notify import (
    NotificationConfig,
    NotificationEvent,
    load_notify_config,
    notify,
    save_notify_config,
)


@pytest.fixture()
def event():
    return NotificationEvent(event_type="snapshot", message="Snapshot taken", metadata={"file": "snap.json"})


@pytest.fixture()
def cfg_file(tmp_path):
    return str(tmp_path / "notify.json")


def test_notify_stdout_prints(event, capsys):
    cfg = NotificationConfig(channel="stdout", target="")
    notify(event, [cfg])
    captured = capsys.readouterr()
    assert "snapshot" in captured.out
    assert "Snapshot taken" in captured.out


def test_notify_file_creates_log(event, tmp_path):
    log = str(tmp_path / "events.log")
    cfg = NotificationConfig(channel="file", target=log)
    notify(event, [cfg])
    lines = Path(log).read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["type"] == "snapshot"
    assert entry["message"] == "Snapshot taken"


def test_notify_file_appends_multiple(event, tmp_path):
    log = str(tmp_path / "events.log")
    cfg = NotificationConfig(channel="file", target=log)
    notify(event, [cfg])
    notify(event, [cfg])
    lines = Path(log).read_text().strip().splitlines()
    assert len(lines) == 2


def test_notify_skips_disabled(event, capsys):
    cfg = NotificationConfig(channel="stdout", target="", enabled=False)
    notify(event, [cfg])
    assert capsys.readouterr().out == ""


def test_notify_filters_by_event_type(event, capsys):
    cfg = NotificationConfig(channel="stdout", target="", events=["diff"])
    notify(event, [cfg])  # event_type is 'snapshot', not 'diff'
    assert capsys.readouterr().out == ""


def test_notify_matches_event_type(event, capsys):
    cfg = NotificationConfig(channel="stdout", target="", events=["snapshot"])
    notify(event, [cfg])
    assert "Snapshot taken" in capsys.readouterr().out


def test_save_and_load_config(cfg_file):
    configs = [
        NotificationConfig(channel="stdout", target="", events=["snapshot"]),
        NotificationConfig(channel="file", target="/tmp/log.txt", enabled=False),
    ]
    save_notify_config(configs, cfg_file)
    loaded = load_notify_config(cfg_file)
    assert len(loaded) == 2
    assert loaded[0].channel == "stdout"
    assert loaded[0].events == ["snapshot"]
    assert loaded[1].enabled is False


def test_load_config_missing_file_returns_empty(tmp_path):
    result = load_notify_config(str(tmp_path / "nonexistent.json"))
    assert result == []


def test_save_config_is_valid_json(cfg_file):
    configs = [NotificationConfig(channel="stdout", target="")]
    save_notify_config(configs, cfg_file)
    data = json.loads(Path(cfg_file).read_text())
    assert isinstance(data, list)
    assert data[0]["channel"] == "stdout"
