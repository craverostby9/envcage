"""Profile management: named collections of required keys and defaults."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Profile:
    name: str
    required_keys: List[str] = field(default_factory=list)
    defaults: Dict[str, str] = field(default_factory=dict)
    description: str = ""


def create_profile(
    name: str,
    required_keys: Optional[List[str]] = None,
    defaults: Optional[Dict[str, str]] = None,
    description: str = "",
) -> Profile:
    """Create a new Profile instance."""
    return Profile(
        name=name,
        required_keys=sorted(set(required_keys or [])),
        defaults=defaults or {},
        description=description,
    )


def save_profile(profile: Profile, path: str) -> None:
    """Persist a profile to a JSON file."""
    data = {
        "name": profile.name,
        "required_keys": profile.required_keys,
        "defaults": profile.defaults,
        "description": profile.description,
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_profile(path: str) -> Profile:
    """Load a profile from a JSON file."""
    data = json.loads(Path(path).read_text())
    return Profile(
        name=data["name"],
        required_keys=data.get("required_keys", []),
        defaults=data.get("defaults", {}),
        description=data.get("description", ""),
    )


def apply_profile(profile: Profile, env: Dict[str, str]) -> Dict[str, str]:
    """Return env merged with profile defaults (env values take precedence)."""
    merged = dict(profile.defaults)
    merged.update(env)
    return merged


def missing_keys(profile: Profile, env: Dict[str, str]) -> List[str]:
    """Return required keys absent from env (after applying defaults)."""
    effective = apply_profile(profile, env)
    return [k for k in profile.required_keys if k not in effective]
