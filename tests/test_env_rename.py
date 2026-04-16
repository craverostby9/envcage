"""Tests for envcage.env_rename."""
import json
import pytest
from pathlib import Path

from envcage.env_rename import rename_keys, rename_snapshot_file


@pytest.fixture
def snap():
    return {
        "meta": {"label": "test"},
        "env": {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_KEY": "abc"},
    }


def test_rename_single_key(snap):
    result = rename_keys(snap, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.snapshot["env"]
    assert "DB_HOST" not in result.snapshot["env"]


def test_rename_preserves_value(snap):
    result = rename_keys(snap, {"DB_HOST": "DATABASE_HOST"})
    assert result.snapshot["env"]["DATABASE_HOST"] == "localhost"


def test_rename_multiple_keys(snap):
    result = rename_keys(snap, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert "DATABASE_HOST" in result.snapshot["env"]
    assert "DATABASE_PORT" in result.snapshot["env"]
    assert len(result.renamed) == 2


def test_missing_key_goes_to_skipped(snap):
    result = rename_keys(snap, {"MISSING_KEY": "NEW_KEY"})
    assert "MISSING_KEY" in result.skipped
    assert "NEW_KEY" not in result.snapshot["env"]


def test_rename_skipped_when_target_exists_no_overwrite(snap):
    result = rename_keys(snap, {"DB_HOST": "APP_KEY"}, overwrite=False)
    assert "DB_HOST" in result.skipped
    assert result.snapshot["env"]["DB_HOST"] == "localhost"


def test_rename_overwrites_when_flag_set(snap):
    result = rename_keys(snap, {"DB_HOST": "APP_KEY"}, overwrite=True)
    assert result.snapshot["env"]["APP_KEY"] == "localhost"
    assert "DB_HOST" not in result.snapshot["env"]


def test_original_snapshot_not_mutated(snap):
    original_keys = set(snap["env"].keys())
    rename_keys(snap, {"DB_HOST": "DATABASE_HOST"})
    assert set(snap["env"].keys()) == original_keys


def test_meta_preserved(snap):
    result = rename_keys(snap, {"DB_HOST": "DATABASE_HOST"})
    assert result.snapshot["meta"] == snap["meta"]


def test_rename_snapshot_file(tmp_path, snap):
    src = tmp_path / "src.json"
    dest = tmp_path / "dest.json"
    src.write_text(json.dumps(snap))

    result = rename_snapshot_file(str(src), str(dest), {"DB_HOST": "DATABASE_HOST"})

    assert dest.exists()
    saved = json.loads(dest.read_text())
    assert "DATABASE_HOST" in saved["env"]
    assert "DB_HOST" not in saved["env"]
    assert result.renamed == {"DB_HOST": "DATABASE_HOST"}


def test_rename_snapshot_file_skipped_reported(tmp_path, snap):
    src = tmp_path / "src.json"
    dest = tmp_path / "dest.json"
    src.write_text(json.dumps(snap))

    result = rename_snapshot_file(str(src), str(dest), {"NOPE": "ALSO_NOPE"})
    assert "NOPE" in result.skipped
