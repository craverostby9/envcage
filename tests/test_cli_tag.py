"""Tests for envcage.cli_tag CLI commands."""

import argparse
import pytest

from envcage.cli_tag import (
    cmd_tag_add,
    cmd_tag_remove,
    cmd_tag_list,
    cmd_tag_find,
)
from envcage.tag import get_tags, find_by_tag


def _args(tag_file, **kwargs):
    ns = argparse.Namespace(tag_file=tag_file, **kwargs)
    return ns


def test_cmd_tag_add_persists_tag(tmp_path, capsys):
    tf = str(tmp_path / "tags.json")
    cmd_tag_add(_args(tf, snapshot="snap_a", tag="production"))
    assert "production" in get_tags("snap_a", tf)


def test_cmd_tag_add_prints_confirmation(tmp_path, capsys):
    tf = str(tmp_path / "tags.json")
    cmd_tag_add(_args(tf, snapshot="snap_a", tag="production"))
    out = capsys.readouterr().out
    assert "snap_a" in out
    assert "production" in out


def test_cmd_tag_remove_removes_tag(tmp_path, capsys):
    tf = str(tmp_path / "tags.json")
    cmd_tag_add(_args(tf, snapshot="snap_a", tag="production"))
    cmd_tag_remove(_args(tf, snapshot="snap_a", tag="production"))
    assert "production" not in get_tags("snap_a", tf)


def test_cmd_tag_list_single_snapshot(tmp_path, capsys):
    tf = strjson")
    cmd_tag_add(_args(tf, snapshot="snap_a", tag="staging"))
    cmd_tag_list(_args(tf, snapshot="snap_a"))
    out = capsys.readouterr().out
    assert "staging" in out


def test_cmd_tag_list_no_tags_message(tmp_path, capsys):
    tf = str(tmp_path / "tags.json")
    cmd_tag_list(_args(tf, snapshot="snap_a"))
    out = capsys.readouterr().out
    assert "No tags" in out


def test_cmd_tag_list_all(tmp_path, capsys):
    tf = str(tmp_path / "tags.json")
    cmd_tag_add(_args(tf, snapshot="snap_a", tag="production"))
    cmd_tag_add(_args(tf, snapshot="snap_b", tag="staging"))
    cmd_tag_list(_args(tf, snapshot=None))
    out = capsys.readouterr().out
    assert "snap_a" in out
    assert "snap_b" in out


def test_cmd_tag_find_prints_matches(tmp_path, capsys):
    tf = str(tmp_path / "tags.json")
    cmd_tag_add(_args(tf, snapshot="snap_a", tag="production"))
    cmd_tag_add(_args(tf, snapshot="snap_b", tag="production"))
    cmd_tag_find(_args(tf, tag="production"))
    out = capsys.readouterr().out
    assert "snap_a" in out
    assert "snap_b" in out


def test_cmd_tag_find_exits_1_when_no_matches(tmp_path):
    tf = str(tmp_path / "tags.json")
    with pytest.raises(SystemExit) as exc_info:
        cmd_tag_find(_args(tf, tag="nonexistent"))
    assert exc_info.value.code == 1
