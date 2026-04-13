"""Encryption utilities for protecting sensitive snapshot values at rest."""

import base64
import hashlib
import json
from typing import Optional

SENTINEL = "enc:"


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """XOR data with a repeating key."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def encrypt_value(value: str, passphrase: str) -> str:
    """Encrypt a single string value. Returns a sentinel-prefixed base64 string."""
    key = _derive_key(passphrase)
    encrypted = _xor_bytes(value.encode(), key)
    encoded = base64.b64encode(encrypted).decode()
    return f"{SENTINEL}{encoded}"


def decrypt_value(value: str, passphrase: str) -> str:
    """Decrypt a sentinel-prefixed encrypted value. Raises ValueError if not encrypted."""
    if not value.startswith(SENTINEL):
        raise ValueError(f"Value does not appear to be encrypted: {value!r}")
    encoded = value[len(SENTINEL):]
    key = _derive_key(passphrase)
    raw = base64.b64decode(encoded.encode())
    return _xor_bytes(raw, key).decode()


def is_encrypted(value: str) -> bool:
    """Return True if the value looks like an encrypted sentinel value."""
    return isinstance(value, str) and value.startswith(SENTINEL)


def encrypt_snapshot(
    snapshot: dict,
    passphrase: str,
    keys: Optional[list] = None,
) -> dict:
    """Return a new snapshot with specified keys (or all) encrypted."""
    result = dict(snapshot)
    targets = keys if keys is not None else list(snapshot.get("env", {}).keys())
    env = dict(snapshot.get("env", {}))
    for k in targets:
        if k in env and not is_encrypted(env[k]):
            env[k] = encrypt_value(env[k], passphrase)
    result["env"] = env
    return result


def decrypt_snapshot(snapshot: dict, passphrase: str) -> dict:
    """Return a new snapshot with all encrypted values decrypted."""
    result = dict(snapshot)
    env = {}
    for k, v in snapshot.get("env", {}).items():
        env[k] = decrypt_value(v, passphrase) if is_encrypted(v) else v
    result["env"] = env
    return result
