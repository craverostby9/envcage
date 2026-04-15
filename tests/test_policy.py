"""Tests for envcage.policy."""
import json
import pytest
from pathlib import Path

from envcage.policy import (
    PolicyResult,
    Policy,
    create_policy,
    save_policy,
    load_policy,
    enforce_policy,
    enforce_policy_file,
)


@pytest.fixture
def env():
    return {
        "APP_NAME": "myapp",
        "APP_ENV": "production",
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "abc123",
        "EMPTY_VAL": "",
    }


def test_create_policy_stores_required_keys():
    p = create_policy(required_keys=["FOO", "BAR"])
    assert "FOO" in p.required_keys
    assert "BAR" in p.required_keys


def test_create_policy_deduplicates_keys():
    p = create_policy(required_keys=["FOO", "FOO", "BAR"])
    assert p.required_keys.count("FOO") == 1


def test_create_policy_stores_forbidden_keys():
    p = create_policy(forbidden_keys=["DEBUG"])
    assert "DEBUG" in p.forbidden_keys


def test_create_policy_stores_prefixes():
    p = create_policy(required_prefixes=["APP_"])
    assert "APP_" in p.required_prefixes


def test_enforce_policy_passes_when_all_required_present(env):
    p = create_policy(required_keys=["APP_NAME", "DATABASE_URL"])
    result = enforce_policy(p, env)
    assert result.passed is True
    assert result.violations == []


def test_enforce_policy_fails_on_missing_required(env):
    p = create_policy(required_keys=["MISSING_KEY"])
    result = enforce_policy(p, env)
    assert result.passed is False
    assert any("MISSING_KEY" in v for v in result.violations)


def test_enforce_policy_fails_on_forbidden_key(env):
    p = create_policy(forbidden_keys=["SECRET_KEY"])
    result = enforce_policy(p, env)
    assert result.passed is False
    assert any("SECRET_KEY" in v for v in result.violations)


def test_enforce_policy_passes_when_forbidden_absent(env):
    p = create_policy(forbidden_keys=["NOT_PRESENT"])
    result = enforce_policy(p, env)
    assert result.passed is True


def test_enforce_policy_required_prefix_found(env):
    p = create_policy(required_prefixes=["APP_"])
    result = enforce_policy(p, env)
    assert result.passed is True


def test_enforce_policy_required_prefix_missing(env):
    p = create_policy(required_prefixes=["MISSING_PREFIX_"])
    result = enforce_policy(p, env)
    assert result.passed is False


def test_enforce_policy_max_empty_values_ok(env):
    p = create_policy(max_empty_values=2)
    result = enforce_policy(p, env)
    assert result.passed is True


def test_enforce_policy_max_empty_values_exceeded(env):
    p = create_policy(max_empty_values=0)
    result = enforce_policy(p, env)
    assert result.passed is False
    assert any("empty" in v for v in result.violations)


def test_save_and_load_policy_roundtrip(tmp_path):
    path = str(tmp_path / "policy.json")
    p = create_policy(
        required_keys=["FOO"],
        forbidden_keys=["BAR"],
        required_prefixes=["APP_"],
        max_empty_values=1,
        description="test policy",
    )
    save_policy(p, path)
    loaded = load_policy(path)
    assert loaded.required_keys == p.required_keys
    assert loaded.forbidden_keys == p.forbidden_keys
    assert loaded.required_prefixes == p.required_prefixes
    assert loaded.max_empty_values == p.max_empty_values
    assert loaded.description == p.description


def test_save_policy_creates_valid_json(tmp_path):
    path = str(tmp_path / "policy.json")
    p = create_policy(required_keys=["KEY"])
    save_policy(p, path)
    data = json.loads(Path(path).read_text())
    assert "required_keys" in data


def test_policy_result_summary_passed():
    r = PolicyResult(passed=True)
    assert "passed" in r.summary().lower()


def test_policy_result_summary_failed():
    r = PolicyResult(passed=False, violations=["Required key missing: FOO"])
    assert "FAILED" in r.summary()
    assert "FOO" in r.summary()


def test_enforce_policy_file(tmp_path):
    import json as _json
    from envcage.snapshot import save, capture

    snap_path = str(tmp_path / "snap.json")
    policy_path = str(tmp_path / "policy.json")

    snap = capture(required_keys=["APP_NAME"], env={"APP_NAME": "test"})
    save(snap, snap_path)

    p = create_policy(required_keys=["APP_NAME"])
    save_policy(p, policy_path)

    result = enforce_policy_file(policy_path, snap_path)
    assert result.passed is True
