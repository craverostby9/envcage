"""Policy enforcement for environment variable snapshots.

A policy defines rules (required keys, forbidden keys, required prefixes,
max allowed empty values, etc.) that a snapshot must satisfy.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envcage.snapshot import load


@dataclass
class PolicyResult:
    passed: bool
    violations: List[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.passed:
            return "Policy check passed."
        lines = [f"Policy check FAILED ({len(self.violations)} violation(s)):"]
        for v in self.violations:
            lines.append(f"  - {v}")
        return "\n".join(lines)


@dataclass
class Policy:
    required_keys: List[str] = field(default_factory=list)
    forbidden_keys: List[str] = field(default_factory=list)
    required_prefixes: List[str] = field(default_factory=list)
    max_empty_values: int = -1  # -1 means unlimited
    description: str = ""


def create_policy(
    required_keys: Optional[List[str]] = None,
    forbidden_keys: Optional[List[str]] = None,
    required_prefixes: Optional[List[str]] = None,
    max_empty_values: int = -1,
    description: str = "",
) -> Policy:
    return Policy(
        required_keys=sorted(set(required_keys or [])),
        forbidden_keys=sorted(set(forbidden_keys or [])),
        required_prefixes=list(required_prefixes or []),
        max_empty_values=max_empty_values,
        description=description,
    )


def save_policy(policy: Policy, path: str) -> None:
    data = {
        "required_keys": policy.required_keys,
        "forbidden_keys": policy.forbidden_keys,
        "required_prefixes": policy.required_prefixes,
        "max_empty_values": policy.max_empty_values,
        "description": policy.description,
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_policy(path: str) -> Policy:
    data = json.loads(Path(path).read_text())
    return Policy(
        required_keys=data.get("required_keys", []),
        forbidden_keys=data.get("forbidden_keys", []),
        required_prefixes=data.get("required_prefixes", []),
        max_empty_values=data.get("max_empty_values", -1),
        description=data.get("description", ""),
    )


def enforce_policy(policy: Policy, env: dict) -> PolicyResult:
    violations: List[str] = []

    for key in policy.required_keys:
        if key not in env:
            violations.append(f"Required key missing: {key}")

    for key in policy.forbidden_keys:
        if key in env:
            violations.append(f"Forbidden key present: {key}")

    for prefix in policy.required_prefixes:
        if not any(k.startswith(prefix) for k in env):
            violations.append(f"No key found with required prefix: {prefix}")

    if policy.max_empty_values >= 0:
        empty_count = sum(1 for v in env.values() if v == "")
        if empty_count > policy.max_empty_values:
            violations.append(
                f"Too many empty values: {empty_count} > {policy.max_empty_values}"
            )

    return PolicyResult(passed=len(violations) == 0, violations=violations)


def enforce_policy_file(policy_path: str, snapshot_path: str) -> PolicyResult:
    policy = load_policy(policy_path)
    snap = load(snapshot_path)
    return enforce_policy(policy, snap.get("env", {}))
