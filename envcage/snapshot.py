"""Snapshot module: capture and persist environment variable sets."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_SNAPSHOT_DIR = Path(".envcage") / "snapshots"


def capture(env: Optional[dict[str, str]] = None) -> dict:
    """Capture the current environment (or a provided dict) as a snapshot."""
    env_vars = env if env is not None else dict(os.environ)
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "variables": env_vars,
    }


def save(snapshot: dict, name: str, snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> Path:
    """Persist a snapshot to disk as a JSON file.

    Args:
        snapshot: The snapshot dict produced by :func:`capture`.
        name: A human-readable label for the snapshot (e.g. "production").
        snapshot_dir: Directory where snapshots are stored.

    Returns:
        The path to the written file.
    """
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    safe_name = name.replace(" ", "_").lower()
    file_path = snapshot_dir / f"{safe_name}.json"
    with file_path.open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, sort_keys=True)
    return file_path


def load(name: str, snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> dict:
    """Load a previously saved snapshot by name.

    Raises:
        FileNotFoundError: If no snapshot with that name exists.
    """
    safe_name = name.replace(" ", "_").lower()
    file_path = snapshot_dir / f"{safe_name}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"Snapshot '{name}' not found at {file_path}")
    with file_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def list_snapshots(snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> list[str]:
    """Return the names of all saved snapshots."""
    if not snapshot_dir.exists():
        return []
    return [p.stem for p in sorted(snapshot_dir.glob("*.json"))]
