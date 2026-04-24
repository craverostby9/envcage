"""Checksum utilities for environment snapshots.

Provides deterministic hashing of snapshot contents so that
identical environments always produce the same checksum and any
change — however small — produces a different one.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

from envcage.snapshot import load


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def _canonical_bytes(env: Dict[str, str]) -> bytes:
    """Return a stable, canonical byte representation of *env*."""
    ordered = {k: env[k] for k in sorted(env)}
    return json.dumps(ordered, separators=(",", ":"), sort_keys=True).encode()


def checksum(env: Dict[str, str], algorithm: str = "sha256") -> str:
    """Return a hex-digest checksum of *env*.

    Parameters
    ----------
    env:
        Mapping of environment variable names to values.
    algorithm:
        Any algorithm accepted by :func:`hashlib.new` (default ``sha256``).
    """
    h = hashlib.new(algorithm)
    h.update(_canonical_bytes(env))
    return h.hexdigest()


def checksum_file(path: str, algorithm: str = "sha256") -> str:
    """Load a snapshot from *path* and return its checksum."""
    snap = load(path)
    return checksum(snap["env"], algorithm=algorithm)


# ---------------------------------------------------------------------------
# Checksum store
# ---------------------------------------------------------------------------

def _load_store(store_path: str) -> Dict[str, str]:
    p = Path(store_path)
    if not p.exists():
        return {}
    return json.loads(p.read_text())


def _save_store(store_path: str, store: Dict[str, str]) -> None:
    Path(store_path).write_text(json.dumps(store, indent=2))


def record_checksum(
    snapshot_path: str,
    store_path: str,
    algorithm: str = "sha256",
) -> str:
    """Compute and persist the checksum for *snapshot_path* in *store_path*.

    Returns the computed checksum string.
    """
    digest = checksum_file(snapshot_path, algorithm=algorithm)
    store = _load_store(store_path)
    store[snapshot_path] = digest
    _save_store(store_path, store)
    return digest


def verify_checksum(
    snapshot_path: str,
    store_path: str,
    algorithm: str = "sha256",
) -> bool:
    """Return *True* if the current checksum matches the stored one."""
    store = _load_store(store_path)
    stored = store.get(snapshot_path)
    if stored is None:
        return False
    current = checksum_file(snapshot_path, algorithm=algorithm)
    return current == stored


def get_stored_checksum(snapshot_path: str, store_path: str) -> Optional[str]:
    """Return the previously recorded checksum, or *None* if absent."""
    return _load_store(store_path).get(snapshot_path)
