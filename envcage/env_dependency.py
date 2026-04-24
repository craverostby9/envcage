"""env_dependency.py — Track and validate dependencies between environment variables.

Some env vars only make sense when others are present (e.g. DB_PASSWORD requires
DB_HOST).  This module lets you define those dependency rules and check a snapshot
against them.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DependencyRule:
    """A single dependency rule: *dependent* requires all keys in *requires*."""

    dependent: str
    requires: List[str]
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "dependent": self.dependent,
            "requires": sorted(self.requires),
            "description": self.description,
        }

    @staticmethod
    def from_dict(d: dict) -> "DependencyRule":
        return DependencyRule(
            dependent=d["dependent"],
            requires=d.get("requires", []),
            description=d.get("description", ""),
        )


@dataclass
class DependencyViolation:
    """A rule that was violated for a particular snapshot."""

    dependent: str
    missing: List[str]  # required keys that are absent

    def to_dict(self) -> dict:
        return {"dependent": self.dependent, "missing": sorted(self.missing)}

    def __str__(self) -> str:
        missing = ", ".join(self.missing)
        return f"{self.dependent!r} requires missing key(s): {missing}"


@dataclass
class DependencyReport:
    """Result of checking a snapshot against a set of dependency rules."""

    violations: List[DependencyViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.is_valid:
            return "All dependency rules satisfied."
        lines = [f"{len(self.violations)} dependency violation(s):"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "valid": self.is_valid,
            "violations": [v.to_dict() for v in self.violations],
        }


# ---------------------------------------------------------------------------
# Rule management
# ---------------------------------------------------------------------------

def create_rule(dependent: str, requires: List[str], description: str = "") -> DependencyRule:
    """Create a new dependency rule."""
    return DependencyRule(
        dependent=dependent,
        requires=sorted(set(requires)),
        description=description,
    )


def save_rules(rules: List[DependencyRule], path: str) -> None:
    """Persist a list of dependency rules to *path* as JSON."""
    data = [r.to_dict() for r in rules]
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_rules(path: str) -> List[DependencyRule]:
    """Load dependency rules from a JSON file."""
    p = Path(path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return [DependencyRule.from_dict(d) for d in data]


# ---------------------------------------------------------------------------
# Checking
# ---------------------------------------------------------------------------

def check_dependencies(
    env: Dict[str, str],
    rules: List[DependencyRule],
) -> DependencyReport:
    """Check *env* against *rules* and return a :class:`DependencyReport`.

    A rule fires (and is checked) only when *dependent* is present in *env*.
    If any of its required keys are absent a :class:`DependencyViolation` is
    recorded.
    """
    violations: List[DependencyViolation] = []
    for rule in rules:
        if rule.dependent not in env:
            # Rule only applies when the dependent key exists.
            continue
        missing = [k for k in rule.requires if k not in env]
        if missing:
            violations.append(DependencyViolation(dependent=rule.dependent, missing=missing))
    return DependencyReport(violations=violations)


def check_dependencies_file(
    snapshot_path: str,
    rules_path: str,
) -> DependencyReport:
    """Convenience wrapper: load snapshot + rules from disk and check."""
    from envcage.snapshot import load  # local import to avoid circular deps

    snap = load(snapshot_path)
    env: Dict[str, str] = snap.get("env", {})
    rules = load_rules(rules_path)
    return check_dependencies(env, rules)
