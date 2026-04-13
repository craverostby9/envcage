"""Template management for envcage.

Allows defining a required set of environment variable keys (a template)
that can be used to validate or scaffold new snapshots.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def create_template(keys: list[str], description: str = "") -> dict[str, Any]:
    """Create a template dict from a list of required keys."""
    return {
        "keys": sorted(set(keys)),
        "description": description,
    }


def save_template(template: dict[str, Any], path: str | Path) -> None:
    """Save a template to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(template, fh, indent=2)
        fh.write("\n")


def load_template(path: str | Path) -> dict[str, Any]:
    """Load a template from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def template_from_snapshot(snapshot: dict[str, Any], description: str = "") -> dict[str, Any]:
    """Derive a template from an existing snapshot (uses its keys, drops values)."""
    keys = list(snapshot.get("env", {}).keys())
    return create_template(keys, description)


def apply_template(template: dict[str, Any], values: dict[str, str]) -> dict[str, Any]:
    """Scaffold a minimal env dict from a template, filling in provided values.

    Keys not present in *values* are set to an empty string.
    """
    return {key: values.get(key, "") for key in template["keys"]}


def missing_keys(template: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    """Return keys required by the template that are absent from the snapshot env."""
    env_keys = set(snapshot.get("env", {}).keys())
    return [k for k in template["keys"] if k not in env_keys]
