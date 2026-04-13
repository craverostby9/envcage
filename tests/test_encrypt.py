"""Tests for envcage.encrypt module."""

import pytest
from envcage.encrypt import (
    encrypt_value,
    decrypt_value,
    is_encrypted,
    encrypt_snapshot,
    decrypt_snapshot,
    SENTINEL,
)

PASS = "supersecret"


def test_encrypt_value_returns_sentinel_prefix():
    result = encrypt_value("hello", PASS)
    assert result.startswith(SENTINEL)


def test_encrypt_value_is_not_plaintext():
    result = encrypt_value("hello", PASS)
    assert "hello" not in result


def test_decrypt_value_round_trips():
    original = "my_secret_value"
    encrypted = encrypt_value(original, PASS)
    assert decrypt_value(encrypted, PASS) == original


def test_decrypt_value_wrong_passphrase_gives_garbage():
    encrypted = encrypt_value("secret", PASS)
    result = decrypt_value(encrypted, "wrongpass")
    assert result != "secret"


def test_decrypt_value_raises_on_plain_string():
    with pytest.raises(ValueError, match="does not appear to be encrypted"):
        decrypt_value("plaintext", PASS)


def test_is_encrypted_true_for_sentinel():
    enc = encrypt_value("val", PASS)
    assert is_encrypted(enc) is True


def test_is_encrypted_false_for_plain():
    assert is_encrypted("plain_value") is False


def test_is_encrypted_false_for_non_string():
    assert is_encrypted(None) is False  # type: ignore


@pytest.fixture
def base_snapshot():
    return {
        "name": "prod",
        "env": {"DB_PASS": "secret123", "API_KEY": "key456", "PORT": "8080"},
    }


def test_encrypt_snapshot_encrypts_all_by_default(base_snapshot):
    result = encrypt_snapshot(base_snapshot, PASS)
    for v in result["env"].values():
        assert is_encrypted(v)


def test_encrypt_snapshot_encrypts_only_specified_keys(base_snapshot):
    result = encrypt_snapshot(base_snapshot, PASS, keys=["DB_PASS"])
    assert is_encrypted(result["env"]["DB_PASS"])
    assert not is_encrypted(result["env"]["API_KEY"])
    assert not is_encrypted(result["env"]["PORT"])


def test_encrypt_snapshot_does_not_double_encrypt(base_snapshot):
    once = encrypt_snapshot(base_snapshot, PASS)
    twice = encrypt_snapshot(once, PASS)
    assert once["env"] == twice["env"]


def test_decrypt_snapshot_restores_all_values(base_snapshot):
    encrypted = encrypt_snapshot(base_snapshot, PASS)
    decrypted = decrypt_snapshot(encrypted, PASS)
    assert decrypted["env"] == base_snapshot["env"]


def test_decrypt_snapshot_leaves_plain_values_untouched(base_snapshot):
    partial = encrypt_snapshot(base_snapshot, PASS, keys=["DB_PASS"])
    decrypted = decrypt_snapshot(partial, PASS)
    assert decrypted["env"]["PORT"] == "8080"
    assert decrypted["env"]["DB_PASS"] == "secret123"


def test_encrypt_snapshot_preserves_metadata(base_snapshot):
    result = encrypt_snapshot(base_snapshot, PASS)
    assert result["name"] == "prod"
