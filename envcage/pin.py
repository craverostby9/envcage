"""Pin module: mark a snapshot as a pinned (stable/reference) version."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_PIN_FILE = ".envcage_pins.json"


def _load_pins(pin_file: str = _DEFAULT_PIN_FILE) -> Dict[str, str]:
    """Load pin store from disk. Returns {label: snapshot_path}."""
    p = Path(pin_file)
    if not p.exists():
        return {}
    with p.open() as fh:
        return json.load(fh)


def _save_pins(pins: Dict[str, str], pin_file: str = _DEFAULT_PIN_FILE) -> None:
    """Persist pin store to disk."""
    with open(pin_file, "w") as fh:
        json.dump(pins, fh, indent=2)


def pin_snapshot(
    label: str,
    snapshot_path: str,
    pin_file: str = _DEFAULT_PIN_FILE,
) -> None:
    """Associate *label* with *snapshot_path* as a pinned reference."""
    pins = _load_pins(pin_file)
    pins[label] = snapshot_path
    _save_pins(pins, pin_file)


def unpin_snapshot(label: str, pin_file: str = _DEFAULT_PIN_FILE) -> bool:
    """Remove a pin by label. Returns True if it existed, False otherwise."""
    pins = _load_pins(pin_file)
    if label not in pins:
        return False
    del pins[label]
    _save_pins(pins, pin_file)
    return True


def get_pin(label: str, pin_file: str = _DEFAULT_PIN_FILE) -> Optional[str]:
    """Return the snapshot path for *label*, or None if not pinned."""
    return _load_pins(pin_file).get(label)


def list_pins(pin_file: str = _DEFAULT_PIN_FILE) -> Dict[str, str]:
    """Return all pins as {label: snapshot_path}."""
    return _load_pins(pin_file)


def pin_labels(pin_file: str = _DEFAULT_PIN_FILE) -> List[str]:
    """Return sorted list of all pin labels."""
    return sorted(_load_pins(pin_file).keys())
