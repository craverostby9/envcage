"""Tests for envcage.env_filter."""
from __future__ import annotations

import pytest

from envcage.env_filter import (
    filter_by_pattern,
    filter_by_prefix,
    filter_empty_values,
    filter_non_sensitive,
    filter_sensitive,
    filter_snapshot,
)


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "myapp",
        "APP_SECRET_KEY": "s3cr3t",
        "DB_PASSWORD": "hunter2",
        "DB_HOST": "localhost",
        "DEBUG": "true",
        "EMPTY_VAR": "",
        "API_TOKEN": "tok123",
    }


def test_filter_by_pattern_basic(sample_env):
    result = filter_by_pattern(sample_env, r"^DB_")
    assert set(result) == {"DB_PASSWORD", "DB_HOST"}


def test_filter_by_pattern_case_insensitive(sample_env):
    result = filter_by_pattern(sample_env, r"app", case_sensitive=False)
    assert "APP_NAME" in result
    assert "APP_SECRET_KEY" in result


def test_filter_by_pattern_case_sensitive_no_match(sample_env):
    result = filter_by_pattern(sample_env, r"app", case_sensitive=True)
    assert result == {}


def test_filter_by_prefix_single(sample_env):
    result = filter_by_prefix(sample_env, ["APP_"])
    assert set(result) == {"APP_NAME", "APP_SECRET_KEY"}


def test_filter_by_prefix_multiple(sample_env):
    result = filter_by_prefix(sample_env, ["APP_", "DB_"])
    assert set(result) == {"APP_NAME", "APP_SECRET_KEY", "DB_PASSWORD", "DB_HOST"}


def test_filter_by_prefix_case_insensitive(sample_env):
    result = filter_by_prefix(sample_env, ["app_"], case_sensitive=False)
    assert "APP_NAME" in result


def test_filter_sensitive(sample_env):
    result = filter_sensitive(sample_env)
    assert "DB_PASSWORD" in result
    assert "APP_SECRET_KEY" in result
    assert "APP_NAME" not in result


def test_filter_non_sensitive(sample_env):
    result = filter_non_sensitive(sample_env)
    assert "APP_NAME" in result
    assert "DB_PASSWORD" not in result


def test_filter_empty_values(sample_env):
    result = filter_empty_values(sample_env)
    assert result == {"EMPTY_VAR": ""}


def test_filter_snapshot_combines_options(sample_env):
    result = filter_snapshot(sample_env, prefixes=["DB_"], sensitive_only=True)
    assert "DB_PASSWORD" in result
    assert "DB_HOST" not in result


def test_filter_snapshot_no_options_returns_all(sample_env):
    result = filter_snapshot(sample_env)
    assert result == sample_env


def test_filter_snapshot_pattern_and_non_sensitive(sample_env):
    result = filter_snapshot(sample_env, pattern=r"^DB_", non_sensitive_only=True)
    assert "DB_HOST" in result
    assert "DB_PASSWORD" not in result
