"""Export snapshots to various formats (dotenv, shell, JSON)."""

from __future__ import annotations

import json
import shlex
from pathlib import Path
from typing import Dict, Literal

from envcage.snapshot import load

ExportFormat = Literal["dotenv", "shell", "json"]


def to_dotenv(env: Dict[str, str]) -> str:
    """Serialize env vars to .env file format."""
    lines = []
    for key in sorted(env):
        value = env[key]
        # Quote values that contain spaces or special characters
        if any(c in value for c in (" ", "\t", "'", '"', "$", "`", "\\")):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def to_shell(env: Dict[str, str]) -> str:
    """Serialize env vars as shell export statements."""
    lines = []
    for key in sorted(env):
        quoted = shlex.quote(env[key])
        lines.append(f"export {key}={quoted}")
    return "\n".join(lines) + ("\n" if lines else "")


def to_json(env: Dict[str, str]) -> str:
    """Serialize env vars as pretty-printed JSON."""
    return json.dumps(env, indent=2, sort_keys=True) + "\n"


def export_snapshot(snapshot_path: str, fmt: ExportFormat = "dotenv") -> str:
    """Load a snapshot file and export it in the requested format."""
    snapshot = load(snapshot_path)
    env: Dict[str, str] = snapshot.get("env", {})

    if fmt == "dotenv":
        return to_dotenv(env)
    elif fmt == "shell":
        return to_shell(env)
    elif fmt == "json":
        return to_json(env)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")


def export_snapshot_to_file(
    snapshot_path: str, output_path: str, fmt: ExportFormat = "dotenv"
) -> None:
    """Export a snapshot to a file in the requested format."""
    content = export_snapshot(snapshot_path, fmt)
    Path(output_path).write_text(content, encoding="utf-8")
