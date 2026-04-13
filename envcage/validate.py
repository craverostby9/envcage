"""Validate environment variable snapshots against a schema of required keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envcage.snapshot import load


@dataclass
class ValidationResult:
    missing: List[str] = field(default_factory=list)
    extra: List[str] = field(default_factory=list)
    invalid: Dict[str, str] = field(default_factory=dict)  # key -> reason

    @property
    def is_valid(self) -> bool:
        return not self.missing and not self.invalid

    def summary(self) -> str:
        lines = []
        if self.missing:
            lines.append(f"Missing keys ({len(self.missing)}): {', '.join(sorted(self.missing))}")
        if self.extra:
            lines.append(f"Extra keys ({len(self.extra)}): {', '.join(sorted(self.extra))}")
        if self.invalid:
            for key, reason in sorted(self.invalid.items()):
                lines.append(f"Invalid '{key}': {reason}")
        if not lines:
            return "All checks passed."
        return "\n".join(lines)


def validate_snapshot(
    snapshot: Dict[str, str],
    required_keys: List[str],
    allowed_extra: bool = True,
    rules: Optional[Dict[str, callable]] = None,
) -> ValidationResult:
    """Validate a snapshot dict against required keys and optional rules.

    Args:
        snapshot: The environment snapshot to validate.
        required_keys: Keys that must be present in the snapshot.
        allowed_extra: If False, keys not in required_keys are reported as extra.
        rules: Optional mapping of key -> callable(value) -> Optional[str].
               The callable should return an error message string or None.
    """
    result = ValidationResult()
    snapshot_keys = set(snapshot.keys())
    required_set = set(required_keys)

    result.missing = sorted(required_set - snapshot_keys)

    if not allowed_extra:
        result.extra = sorted(snapshot_keys - required_set)

    if rules:
        for key, rule in rules.items():
            if key in snapshot:
                error = rule(snapshot[key])
                if error:
                    result.invalid[key] = error

    return result


def validate_snapshot_file(
    path: str,
    required_keys: List[str],
    allowed_extra: bool = True,
    rules: Optional[Dict[str, callable]] = None,
) -> ValidationResult:
    """Load a snapshot from a file and validate it."""
    snapshot = load(path)
    return validate_snapshot(snapshot, required_keys, allowed_extra=allowed_extra, rules=rules)
