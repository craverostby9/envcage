"""Tests for envcage.env_signature."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.env_signature import (
    SIGNATURE_KEY,
    SignatureResult,
    sign_snapshot,
    sign_snapshot_file,
    verify_snapshot,
    verify_snapshot_file,
)


@pytest.fixture()
def simple_env() -> dict:
    return {"APP_ENV": "production", "DB_HOST": "localhost", "SECRET_KEY": "abc123"}


@pytest.fixture()
def snap_file(tmp_path: Path, simple_env: dict) -> Path:
    p = tmp_path / "snap.json"
    p.write_text(json.dumps(simple_env))
    return p


# --- sign_snapshot ---

def test_sign_snapshot_returns_hex_string(simple_env: dict) -> None:
    sig = sign_snapshot(simple_env, "secret")
    assert isinstance(sig, str)
    assert len(sig) == 64  # SHA-256 hex


def test_sign_snapshot_is_deterministic(simple_env: dict) -> None:
    sig1 = sign_snapshot(simple_env, "secret")
    sig2 = sign_snapshot(simple_env, "secret")
    assert sig1 == sig2


def test_sign_snapshot_differs_with_different_passphrase(simple_env: dict) -> None:
    sig1 = sign_snapshot(simple_env, "secret")
    sig2 = sign_snapshot(simple_env, "other")
    assert sig1 != sig2


def test_sign_snapshot_differs_with_different_env(simple_env: dict) -> None:
    sig1 = sign_snapshot(simple_env, "secret")
    modified = dict(simple_env, EXTRA_KEY="new")
    sig2 = sign_snapshot(modified, "secret")
    assert sig1 != sig2


def test_sign_snapshot_ignores_embedded_signature_key(simple_env: dict) -> None:
    """Signing should be stable regardless of an existing SIGNATURE_KEY."""
    sig1 = sign_snapshot(simple_env, "secret")
    with_sig = dict(simple_env, **{SIGNATURE_KEY: "old_sig"})
    sig2 = sign_snapshot(with_sig, "secret")
    assert sig1 == sig2


# --- verify_snapshot ---

def test_verify_snapshot_valid(simple_env: dict) -> None:
    sig = sign_snapshot(simple_env, "secret")
    signed = dict(simple_env, **{SIGNATURE_KEY: sig})
    result = verify_snapshot(signed, "secret")
    assert result.valid is True
    assert result.reason == ""


def test_verify_snapshot_invalid_passphrase(simple_env: dict) -> None:
    sig = sign_snapshot(simple_env, "secret")
    signed = dict(simple_env, **{SIGNATURE_KEY: sig})
    result = verify_snapshot(signed, "wrong")
    assert result.valid is False
    assert "mismatch" in result.reason.lower()


def test_verify_snapshot_missing_signature(simple_env: dict) -> None:
    result = verify_snapshot(simple_env, "secret")
    assert result.valid is False
    assert "no signature" in result.reason.lower()


def test_verify_snapshot_tampered_value(simple_env: dict) -> None:
    sig = sign_snapshot(simple_env, "secret")
    tampered = dict(simple_env, APP_ENV="staging", **{SIGNATURE_KEY: sig})
    result = verify_snapshot(tampered, "secret")
    assert result.valid is False


# --- file helpers ---

def test_sign_snapshot_file_embeds_signature(snap_file: Path) -> None:
    sign_snapshot_file(str(snap_file), "secret")
    data = json.loads(snap_file.read_text())
    assert SIGNATURE_KEY in data


def test_sign_snapshot_file_returns_result(snap_file: Path) -> None:
    result = sign_snapshot_file(str(snap_file), "secret")
    assert isinstance(result, SignatureResult)
    assert result.valid is True
    assert len(result.signature) == 64


def test_verify_snapshot_file_passes_after_signing(snap_file: Path) -> None:
    sign_snapshot_file(str(snap_file), "mysecret")
    result = verify_snapshot_file(str(snap_file), "mysecret")
    assert result.valid is True


def test_verify_snapshot_file_fails_wrong_passphrase(snap_file: Path) -> None:
    sign_snapshot_file(str(snap_file), "mysecret")
    result = verify_snapshot_file(str(snap_file), "wrong")
    assert result.valid is False


def test_sign_snapshot_file_optional_output(snap_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "signed.json"
    sign_snapshot_file(str(snap_file), "secret", output=str(out))
    assert out.exists()
    data = json.loads(out.read_text())
    assert SIGNATURE_KEY in data
