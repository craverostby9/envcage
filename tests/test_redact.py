"""Tests for envcage.redact module."""

import pytest

from envcage.redact import (
    DEFAULT_SENSITIVE_PATTERNS,
    REDACT_PLACEHOLDER,
    is_sensitive,
    redact_snapshot,
    redacted_keys,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "SECRET",
    "DB_PASSWORD",
    "API_TOKEN",
    "GITHUB_API_KEY",
    "PRIVATE_KEY",
    "AUTH_HEADER",
    "AWS_SECRET_ACCESS_KEY",
    "user_credentials",
])
def test_is_sensitive_returns_true_for_sensitive_keys(key):
    assert is_sensitive(key) is True


@pytest.mark.parametrize("key", [
    "HOME",
    "PATH",
    "USER",
    "PORT",
    "LOG_LEVEL",
    "APP_NAME",
])
def test_is_sensitive_returns_false_for_safe_keys(key):
    assert is_sensitive(key) is False


def test_is_sensitive_respects_custom_patterns():
    assert is_sensitive("MY_CUSTOM_FIELD", patterns=[r"(?i).*custom.*"]) is True
    assert is_sensitive("HOME", patterns=[r"(?i).*custom.*"]) is False


def test_is_sensitive_empty_patterns_never_matches():
    assert is_sensitive("SECRET", patterns=[]) is False


# ---------------------------------------------------------------------------
# redact_snapshot
# ---------------------------------------------------------------------------

@pytest.fixture
def mixed_snapshot():
    return {
        "HOME": "/home/user",
        "DB_PASSWORD": "s3cr3t",
        "PORT": "8080",
        "API_TOKEN": "tok_abc123",
        "APP_NAME": "envcage",
    }


def test_redact_snapshot_replaces_sensitive_values(mixed_snapshot):
    result = redact_snapshot(mixed_snapshot)
    assert result["DB_PASSWORD"] == REDACT_PLACEHOLDER
    assert result["API_TOKEN"] == REDACT_PLACEHOLDER


def test_redact_snapshot_preserves_safe_values(mixed_snapshot):
    result = redact_snapshot(mixed_snapshot)
    assert result["HOME"] == "/home/user"
    assert result["PORT"] == "8080"
    assert result["APP_NAME"] == "envcage"


def test_redact_snapshot_does_not_mutate_original(mixed_snapshot):
    original_copy = dict(mixed_snapshot)
    redact_snapshot(mixed_snapshot)
    assert mixed_snapshot == original_copy


def test_redact_snapshot_custom_placeholder(mixed_snapshot):
    result = redact_snapshot(mixed_snapshot, placeholder="[hidden]")
    assert result["DB_PASSWORD"] == "[hidden]"


def test_redact_snapshot_empty_snapshot():
    assert redact_snapshot({}) == {}


# ---------------------------------------------------------------------------
# redacted_keys
# ---------------------------------------------------------------------------

def test_redacted_keys_returns_sorted_list(mixed_snapshot):
    keys = redacted_keys(mixed_snapshot)
    assert keys == sorted(keys)
    assert "DB_PASSWORD" in keys
    assert "API_TOKEN" in keys


def test_redacted_keys_excludes_safe_keys(mixed_snapshot):
    keys = redacted_keys(mixed_snapshot)
    assert "HOME" not in keys
    assert "PORT" not in keys


def test_redacted_keys_empty_snapshot():
    assert redacted_keys({}) == []
