"""High-level helpers to save and load encrypted snapshots from disk."""

import json
from pathlib import Path
from typing import Optional

from envcage.encrypt import encrypt_snapshot, decrypt_snapshot
from envcage.snapshot import capture, save, load
from envcage.redact import is_sensitive


def save_encrypted(
    snapshot: dict,
    path: str,
    passphrase: str,
    keys: Optional[list] = None,
) -> Path:
    """Encrypt snapshot values then write to *path* as JSON.

    If *keys* is None, only keys detected as sensitive are encrypted.
    Pass an explicit list to override.
    """
    if keys is None:
        keys = [k for k in snapshot.get("env", {}) if is_sensitive(k)]
    encrypted = encrypt_snapshot(snapshot, passphrase, keys=keys)
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(encrypted, indent=2))
    return dest


def load_encrypted(path: str, passphrase: str) -> dict:
    """Load an encrypted snapshot file and return the decrypted snapshot dict."""
    raw = json.loads(Path(path).read_text())
    return decrypt_snapshot(raw, passphrase)


def capture_and_save_encrypted(
    path: str,
    passphrase: str,
    required_keys: Optional[list] = None,
    env: Optional[dict] = None,
    name: Optional[str] = None,
    keys: Optional[list] = None,
) -> dict:
    """Capture current environment, encrypt sensitive values, and persist.

    Returns the *unencrypted* snapshot dict for immediate use.
    """
    snap = capture(required_keys=required_keys or [], env=env, name=name)
    save_encrypted(snap, path, passphrase, keys=keys)
    return snap
