"""Tests for envcage.env_mask."""
import pytest
from envcage.env_mask import mask_value, mask_snapshot, MaskResult


# ---------------------------------------------------------------------------
# mask_value
# ---------------------------------------------------------------------------

def test_mask_value_hides_prefix():
    result = mask_value("supersecret", visible=4)
    assert result.endswith("cret")
    assert result.startswith("*")


def test_mask_value_full_mask_when_short():
    result = mask_value("abc", visible=4)
    assert result == "***"


def test_mask_value_exact_visible_length():
    result = mask_value("abcd", visible=4)
    assert result == "****"


def test_mask_value_custom_char():
    result = mask_value("password", visible=2, char="#")
    assert "#" in result
    assert result.endswith("rd")


def test_mask_value_zero_visible():
    result = mask_value("hello", visible=0)
    assert result == "*****"


# ---------------------------------------------------------------------------
# mask_snapshot
# ---------------------------------------------------------------------------

@pytest.fixture()
def mixed_env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t!",
        "API_KEY": "abcdef1234",
        "PORT": "8080",
    }


def test_mask_snapshot_returns_mask_result(mixed_env):
    result = mask_snapshot(mixed_env)
    assert isinstance(result, MaskResult)


def test_mask_snapshot_sensitive_keys_are_masked(mixed_env):
    result = mask_snapshot(mixed_env)
    assert result.env["DB_PASSWORD"] != "s3cr3t!"
    assert result.env["API_KEY"] != "abcdef1234"


def test_mask_snapshot_non_sensitive_keys_unchanged(mixed_env):
    result = mask_snapshot(mixed_env)
    assert result.env["APP_NAME"] == "myapp"
    assert result.env["PORT"] == "8080"


def test_mask_snapshot_masked_keys_listed(mixed_env):
    result = mask_snapshot(mixed_env)
    assert "DB_PASSWORD" in result.masked_keys
    assert "API_KEY" in result.masked_keys


def test_mask_snapshot_non_sensitive_not_in_masked_keys(mixed_env):
    result = mask_snapshot(mixed_env)
    assert "APP_NAME" not in result.masked_keys
    assert "PORT" not in result.masked_keys


def test_mask_snapshot_original_keys_preserved(mixed_env):
    result = mask_snapshot(mixed_env)
    assert set(result.original_keys) == set(mixed_env.keys())


def test_mask_snapshot_custom_visible(mixed_env):
    result = mask_snapshot(mixed_env, visible=2)
    assert result.env["DB_PASSWORD"].endswith("t!")


def test_mask_snapshot_custom_patterns():
    env = {"MY_CUSTOM_TOKEN": "abc123", "SAFE": "visible"}
    result = mask_snapshot(env, patterns=[r"TOKEN"])
    assert result.env["MY_CUSTOM_TOKEN"] != "abc123"
    assert result.env["SAFE"] == "visible"


def test_mask_snapshot_empty_env():
    result = mask_snapshot({})
    assert result.env == {}
    assert result.masked_keys == []
