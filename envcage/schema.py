"""Schema validation for environment variable snapshots.

Allows defining expected types, patterns, and constraints for env var values.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class SchemaRule:
    key: str
    required: bool = True
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    allowed_values: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "required": self.required,
            "pattern": self.pattern,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "allowed_values": self.allowed_values,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SchemaRule":
        return cls(
            key=data["key"],
            required=data.get("required", True),
            pattern=data.get("pattern"),
            min_length=data.get("min_length"),
            max_length=data.get("max_length"),
            allowed_values=data.get("allowed_values", []),
        )


@dataclass
class SchemaViolation:
    key: str
    message: str


@dataclass
class SchemaReport:
    violations: List[SchemaViolation] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    def summary(self) -> str:
        if self.is_valid:
            return "Schema check passed."
        lines = [f"Schema violations ({len(self.violations)}):"]
        for v in self.violations:
            lines.append(f"  [{v.key}] {v.message}")
        return "\n".join(lines)


def create_schema(rules: List[SchemaRule]) -> Dict[str, SchemaRule]:
    return {r.key: r for r in rules}


def save_schema(rules: List[SchemaRule], path: str) -> None:
    Path(path).write_text(json.dumps([r.to_dict() for r in rules], indent=2))


def load_schema(path: str) -> List[SchemaRule]:
    data = json.loads(Path(path).read_text())
    return [SchemaRule.from_dict(d) for d in data]


def validate_schema(env: Dict[str, str], rules: List[SchemaRule]) -> SchemaReport:
    violations: List[SchemaViolation] = []
    for rule in rules:
        value = env.get(rule.key)
        if value is None:
            if rule.required:
                violations.append(SchemaViolation(rule.key, "required key is missing"))
            continue
        if rule.pattern and not re.fullmatch(rule.pattern, value):
            violations.append(SchemaViolation(rule.key, f"value does not match pattern '{rule.pattern}'"))
        if rule.min_length is not None and len(value) < rule.min_length:
            violations.append(SchemaViolation(rule.key, f"value too short (min {rule.min_length})"))
        if rule.max_length is not None and len(value) > rule.max_length:
            violations.append(SchemaViolation(rule.key, f"value too long (max {rule.max_length})"))
        if rule.allowed_values and value not in rule.allowed_values:
            violations.append(SchemaViolation(rule.key, f"value '{value}' not in allowed values"))
    return SchemaReport(violations=violations)


def validate_schema_file(snapshot_path: str, schema_path: str) -> SchemaReport:
    from envcage.snapshot import load
    snap = load(snapshot_path)
    rules = load_schema(schema_path)
    return validate_schema(snap["env"], rules)
