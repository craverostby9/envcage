"""Tests for envcage.env_stats."""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from envcage.env_stats import SnapshotStats, compute_stats, stats_from_file, summary


@pytest.fixture
def simple_env():
    return {
        "HOME": "/home/user",
        "PATH": "/usr/bin:/bin",
        "SECRET_KEY": "s3cr3t",
        "API_TOKEN": "tok123",
        "EMPTY_VAR": "",
        "DUPLICATE_A": "same",
        "DUPLICATE_B": "same",
    }


def test_total_keys(simple_env):
    stats = compute_stats(simple_env)
    assert stats.total_keys == len(simple_env)


def test_sensitive_keys_detected(simple_env):
    stats = compute_stats(simple_env)
    # SECRET_KEY and API_TOKEN should be flagged
    assert stats.sensitive_keys >= 2


def test_empty_values_counted(simple_env):
    stats = compute_stats(simple_env)
    assert stats.empty_values == 1


def test_duplicate_values_counted(simple_env):
    stats = compute_stats(simple_env)
    # "same" appears twice
    assert stats.duplicate_values >= 1


def test_unique_values_counted(simple_env):
    stats = compute_stats(simple_env)
    # HOME, PATH, s3cr3t, tok123, "" are unique; "same" is not
    assert stats.unique_values >= 4


def test_longest_key(simple_env):
    stats = compute_stats(simple_env)
    assert stats.longest_key == max(simple_env.keys(), key=len)


def test_longest_value_key(simple_env):
    stats = compute_stats(simple_env)
    expected = max(simple_env.keys(), key=lambda k: len(simple_env[k]))
    assert stats.longest_value_key == expected


def test_empty_env_returns_zero_stats():
    stats = compute_stats({})
    assert stats.total_keys == 0
    assert stats.sensitive_keys == 0
    assert stats.empty_values == 0
    assert stats.longest_key == ""


def test_as_dict_has_expected_keys(simple_env):
    stats = compute_stats(simple_env)
    d = stats.as_dict()
    for key in ("total_keys", "sensitive_keys", "empty_values",
                "unique_values", "duplicate_values",
                "longest_key", "longest_value_key"):
        assert key in d


def test_stats_from_file(tmp_path, simple_env):
    snap_path = str(tmp_path / "snap.json")
    with open(snap_path, "w") as f:
        json.dump({"env": simple_env, "keys": list(simple_env)}, f)
    stats = stats_from_file(snap_path)
    assert stats.total_keys == len(simple_env)


def test_summary_is_string(simple_env):
    stats = compute_stats(simple_env)
    result = summary(stats)
    assert isinstance(result, str)
    assert "Total keys" in result
    assert "Sensitive keys" in result
