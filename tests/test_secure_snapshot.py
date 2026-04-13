"""Tests for envcage.secure_snapshot module."""

import json
import pytest
from pathlib import Path

from envcage.secure_snapshot import save_encrypted, load_encrypted, capture_and_save_encrypted
from envcage.encrypt import is_encrypted

PASS = "testpass"


@pytest.fixture
def snap():
    return {
        "name": "test",
        "env": {
            "DATABASE_PASSWORD": "secret",
            "API_SECRET": "topsecret",
            "PORT": "3000",
            "HOST": "localhost",
        },
    }


def test_save_encrypted_creates_file(tmp_path, snap):
    dest = tmp_path / "snap.json"
    result = save_encrypted(snap, str(dest), PASS)
    assert result.exists()


def test_save_encrypted_file_is_valid_json(tmp_path, snap):
    dest = tmp_path / "snap.json"
    save_encrypted(snap, str(dest), PASS)
    data = json.loads(dest.read_text())
    assert "env" in data


def test_save_encrypted_sensitive_keys_are_encrypted(tmp_path, snap):
    dest = tmp_path / "snap.json"
    save_encrypted(snap, str(dest), PASS)
    data = json.loads(dest.read_text())
    assert is_encrypted(data["env"]["DATABASE_PASSWORD"])
    assert is_encrypted(data["env"]["API_SECRET"])


def test_save_encrypted_non_sensitive_keys_are_plain(tmp_path, snap):
    dest = tmp_path / "snap.json"
    save_encrypted(snap, str(dest), PASS)
    data = json.loads(dest.read_text())
    assert not is_encrypted(data["env"]["PORT"])
    assert not is_encrypted(data["env"]["HOST"])


def test_save_encrypted_explicit_keys(tmp_path, snap):
    dest = tmp_path / "snap.json"
    save_encrypted(snap, str(dest), PASS, keys=["PORT"])
    data = json.loads(dest.read_text())
    assert is_encrypted(data["env"]["PORT"])
    assert not is_encrypted(data["env"]["HOST"])


def test_load_encrypted_round_trips(tmp_path, snap):
    dest = tmp_path / "snap.json"
    save_encrypted(snap, str(dest), PASS)
    loaded = load_encrypted(str(dest), PASS)
    assert loaded["env"] == snap["env"]


def test_load_encrypted_wrong_pass_gives_wrong_values(tmp_path, snap):
    dest = tmp_path / "snap.json"
    save_encrypted(snap, str(dest), PASS)
    loaded = load_encrypted(str(dest), "wrongpass")
    assert loaded["env"]["DATABASE_PASSWORD"] != snap["env"]["DATABASE_PASSWORD"]


def test_capture_and_save_encrypted(tmp_path, monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "mysecret")
    monkeypatch.setenv("APP_PORT", "9000")
    dest = str(tmp_path / "env.json")
    result = capture_and_save_encrypted(
        dest, PASS, required_keys=["SECRET_KEY", "APP_PORT"]
    )
    assert result["env"]["SECRET_KEY"] == "mysecret"
    on_disk = json.loads(Path(dest).read_text())
    assert is_encrypted(on_disk["env"]["SECRET_KEY"])
