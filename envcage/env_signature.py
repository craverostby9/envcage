"""env_signature.py — Sign and verify environment snapshots using HMAC."""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

SIGNATURE_KEY = "_envcage_sig"


@dataclass
class SignatureResult:
    snapshot_path: str
    signature: str
    valid: bool
    reason: str = ""


def _canonical_bytes(env: dict) -> bytes:
    """Return deterministic bytes for an env dict (excluding signature key)."""
    clean = {k: v for k, v in sorted(env.items()) if k != SIGNATURE_KEY}
    return json.dumps(clean, sort_keys=True, separators=(",", ":")).encode()


def sign_snapshot(env: dict, passphrase: str) -> str:
    """Return HMAC-SHA256 hex signature for the given snapshot env."""
    key = passphrase.encode()
    data = _canonical_bytes(env)
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_snapshot(env: dict, passphrase: str) -> SignatureResult:
    """Verify the embedded signature in an env snapshot."""
    sig = env.get(SIGNATURE_KEY)
    if sig is None:
        return SignatureResult(
            snapshot_path="",
            signature="",
            valid=False,
            reason="No signature found in snapshot.",
        )
    expected = sign_snapshot(env, passphrase)
    valid = hmac.compare_digest(sig, expected)
    return SignatureResult(
        snapshot_path="",
        signature=sig,
        valid=valid,
        reason="" if valid else "Signature mismatch — snapshot may have been tampered with.",
    )


def sign_snapshot_file(path: str, passphrase: str, output: Optional[str] = None) -> SignatureResult:
    """Load a snapshot file, embed the signature, and write it out."""
    p = Path(path)
    env: dict = json.loads(p.read_text())
    sig = sign_snapshot(env, passphrase)
    env[SIGNATURE_KEY] = sig
    out_path = Path(output) if output else p
    out_path.write_text(json.dumps(env, indent=2))
    return SignatureResult(snapshot_path=str(out_path), signature=sig, valid=True)


def verify_snapshot_file(path: str, passphrase: str) -> SignatureResult:
    """Load a snapshot file and verify its embedded signature."""
    p = Path(path)
    env: dict = json.loads(p.read_text())
    result = verify_snapshot(env, passphrase)
    result.snapshot_path = str(p)
    return result
