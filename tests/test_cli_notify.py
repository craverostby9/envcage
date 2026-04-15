"""Tests for envcage.cli_notify."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envcage.cli_notify import cmd_notify_add, cmd_notify_list, cmd_notify_remove
from envcage.notify import load_notify_config, save_notify_config, NotificationConfig


def _args(**kwargs):
    ns = argparse.Namespace(config="")
    for k, v in kwargs.items():
        setattr(ns, k, v)
    return ns


@pytest.fixture()
def cfg_file(tmp_path):
    return str(tmp_path / "notify.json")


def test_cmd_notify_add_persists(cfg_file, capsys):
    args = _args(config=cfg_file, channel="stdout", target="", events="")
    cmd_notify_add(args)
    loaded = load_notify_config(cfg_file)
    assert len(loaded) == 1
    assert loaded[0].channel == "stdout"


def test_cmd_notify_add_prints_confirmation(cfg_file, capsys):
    args = _args(config=cfg_file, channel="file", target="/tmp/log.txt", events="")
    cmd_notify_add(args)
    out = capsys.readouterr().out
    assert "file" in out
    assert "/tmp/log.txt" in out


def test_cmd_notify_add_stores_events(cfg_file):
    args = _args(config=cfg_file, channel="stdout", target="", events="snapshot,diff")
    cmd_notify_add(args)
    loaded = load_notify_config(cfg_file)
    assert loaded[0].events == ["snapshot", "diff"]


def test_cmd_notify_list_empty(cfg_file, capsys):
    args = _args(config=cfg_file)
    cmd_notify_list(args)
    assert "No notification" in capsys.readouterr().out


def test_cmd_notify_list_shows_entries(cfg_file, capsys):
    save_notify_config(
        [NotificationConfig(channel="webhook", target="http://example.com", events=["diff"])],
        cfg_file,
    )
    args = _args(config=cfg_file)
    cmd_notify_list(args)
    out = capsys.readouterr().out
    assert "webhook" in out
    assert "http://example.com" in out
    assert "diff" in out


def test_cmd_notify_remove_removes_entry(cfg_file):
    save_notify_config(
        [
            NotificationConfig(channel="stdout", target=""),
            NotificationConfig(channel="file", target="/tmp/x.log"),
        ],
        cfg_file,
    )
    args = _args(config=cfg_file, index=1)
    cmd_notify_remove(args)
    loaded = load_notify_config(cfg_file)
    assert len(loaded) == 1
    assert loaded[0].channel == "file"


def test_cmd_notify_remove_invalid_index_exits(cfg_file):
    save_notify_config([NotificationConfig(channel="stdout", target="")], cfg_file)
    args = _args(config=cfg_file, index=99)
    with pytest.raises(SystemExit):
        cmd_notify_remove(args)
