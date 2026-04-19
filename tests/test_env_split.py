"""Tests for envcage.env_split."""
import pytest
from envcage.env_split import split_by_prefix, split_by_keys, split_snapshot_file, SplitResult
from envcage.snapshot import save
import json, os


@pytest.fixture
def sample_env():
    return {
        "APP_HOST": "localhost",
        "APP_PORT": "8080",
        "DB_HOST": "db.local",
        "DB_PORT": "5432",
        "LOG_LEVEL": "info",
    }


def test_split_by_prefix_partitions_keys(sample_env):
    result = split_by_prefix(sample_env, ["APP_", "DB_"])
    assert "APP_HOST" in result.parts["APP_"]
    assert "DB_HOST" in result.parts["DB_"]


def test_split_by_prefix_unmatched(sample_env):
    result = split_by_prefix(sample_env, ["APP_", "DB_"])
    assert "LOG_LEVEL" in result.unmatched


def test_split_by_prefix_strip_prefix(sample_env):
    result = split_by_prefix(sample_env, ["APP_"], strip_prefix=True)
    assert "HOST" in result.parts["APP_"]
    assert "PORT" in result.parts["APP_"]


def test_split_by_prefix_total_keys(sample_env):
    result = split_by_prefix(sample_env, ["APP_", "DB_"])
    assert result.total_keys == len(sample_env)


def test_split_by_prefix_total_parts(sample_env):
    result = split_by_prefix(sample_env, ["APP_", "DB_"])
    assert result.total_parts == 2


def test_split_by_keys_assigns_correctly(sample_env):
    groups = {"web": ["APP_HOST", "APP_PORT"], "database": ["DB_HOST", "DB_PORT"]}
    result = split_by_keys(sample_env, groups)
    assert result.parts["web"]["APP_HOST"] == "localhost"
    assert result.parts["database"]["DB_PORT"] == "5432"


def test_split_by_keys_unmatched(sample_env):
    groups = {"web": ["APP_HOST"]}
    result = split_by_keys(sample_env, groups)
    assert "LOG_LEVEL" in result.unmatched
    assert "DB_HOST" in result.unmatched


def test_split_by_keys_missing_key_skipped(sample_env):
    groups = {"web": ["APP_HOST", "NONEXISTENT"]}
    result = split_by_keys(sample_env, groups)
    assert "NONEXISTENT" not in result.parts["web"]


def test_split_snapshot_file_creates_outputs(tmp_path, sample_env):
    src = str(tmp_path / "source.json")
    save({"env": sample_env, "required": []}, src)
    result = split_snapshot_file(src, prefixes=["APP_", "DB_"], output_dir=str(tmp_path))
    assert (tmp_path / "APP.json").exists()
    assert (tmp_path / "DB.json").exists()


def test_split_snapshot_file_raises_without_options(tmp_path, sample_env):
    src = str(tmp_path / "source.json")
    save({"env": sample_env, "required": []}, src)
    with pytest.raises(ValueError):
        split_snapshot_file(src, output_dir=str(tmp_path))
