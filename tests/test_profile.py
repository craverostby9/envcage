"""Tests for envcage.profile."""

import json
import pytest
from pathlib import Path

from envcage.profile import (
    Profile,
    create_profile,
    save_profile,
    load_profile,
    apply_profile,
    missing_keys,
)


# ---------------------------------------------------------------------------
# create_profile
# ---------------------------------------------------------------------------

def test_create_profile_stores_name():
    p = create_profile("production")
    assert p.name == "production"


def test_create_profile_deduplicates_and_sorts_keys():
    p = create_profile("prod", required_keys=["Z_KEY", "A_KEY", "A_KEY"])
    assert p.required_keys == ["A_KEY", "Z_KEY"]


def test_create_profile_empty_defaults_by_default():
    p = create_profile("prod")
    assert p.defaults == {}


def test_create_profile_stores_description():
    p = create_profile("staging", description="Staging env")
    assert p.description == "Staging env"


def test_create_profile_stores_defaults():
    p = create_profile("dev", defaults={"LOG_LEVEL": "DEBUG"})
    assert p.defaults["LOG_LEVEL"] == "DEBUG"


# ---------------------------------------------------------------------------
# save / load round-trip
# ---------------------------------------------------------------------------

def test_save_creates_file(tmp_path):
    p = create_profile("prod", required_keys=["DB_URL"])
    dest = str(tmp_path / "profile.json")
    save_profile(p, dest)
    assert Path(dest).exists()


def test_save_file_is_valid_json(tmp_path):
    p = create_profile("prod", required_keys=["DB_URL"])
    dest = str(tmp_path / "profile.json")
    save_profile(p, dest)
    data = json.loads(Path(dest).read_text())
    assert "required_keys" in data


def test_load_round_trips(tmp_path):
    p = create_profile(
        "prod",
        required_keys=["DB_URL", "SECRET"],
        defaults={"LOG_LEVEL": "INFO"},
        description="Production",
    )
    dest = str(tmp_path / "profile.json")
    save_profile(p, dest)
    loaded = load_profile(dest)
    assert loaded.name == p.name
    assert loaded.required_keys == p.required_keys
    assert loaded.defaults == p.defaults
    assert loaded.description == p.description


# ---------------------------------------------------------------------------
# apply_profile
# ---------------------------------------------------------------------------

def test_apply_profile_fills_defaults():
    p = create_profile("dev", defaults={"LOG_LEVEL": "DEBUG", "PORT": "8080"})
    result = apply_profile(p, {})
    assert result["LOG_LEVEL"] == "DEBUG"
    assert result["PORT"] == "8080"


def test_apply_profile_env_overrides_defaults():
    p = create_profile("dev", defaults={"LOG_LEVEL": "DEBUG"})
    result = apply_profile(p, {"LOG_LEVEL": "WARNING"})
    assert result["LOG_LEVEL"] == "WARNING"


def test_apply_profile_does_not_mutate_env():
    p = create_profile("dev", defaults={"EXTRA": "yes"})
    env = {"MY_VAR": "1"}
    apply_profile(p, env)
    assert "EXTRA" not in env


# ---------------------------------------------------------------------------
# missing_keys
# ---------------------------------------------------------------------------

def test_missing_keys_detects_absent_required():
    p = create_profile("prod", required_keys=["DB_URL", "SECRET"])
    assert "DB_URL" in missing_keys(p, {"SECRET": "x"})


def test_missing_keys_empty_when_all_present():
    p = create_profile("prod", required_keys=["DB_URL"])
    assert missing_keys(p, {"DB_URL": "postgres://..."}) == []


def test_missing_keys_satisfied_by_defaults():
    p = create_profile(
        "dev",
        required_keys=["LOG_LEVEL"],
        defaults={"LOG_LEVEL": "DEBUG"},
    )
    assert missing_keys(p, {}) == []
