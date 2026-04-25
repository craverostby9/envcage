"""Infer and validate the type of environment variable values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# Ordered from most specific to least specific
_BOOL_TRUE = re.compile(r'^(true|yes|1|on)$', re.IGNORECASE)
_BOOL_FALSE = re.compile(r'^(false|no|0|off)$', re.IGNORECASE)
_INT = re.compile(r'^-?\d+$')
_FLOAT = re.compile(r'^-?\d+\.\d+$')
_URL = re.compile(r'^https?://', re.IGNORECASE)
_EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
_PATH = re.compile(r'^[/~\\]|^[A-Za-z]:\\')

INFERRED_TYPES = ("bool", "int", "float", "url", "email", "path", "empty", "string")


@dataclass
class TypeInference:
    key: str
    value: str
    inferred_type: str
    expected_type: Optional[str] = None
    mismatch: bool = False

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "inferred_type": self.inferred_type,
            "expected_type": self.expected_type,
            "mismatch": self.mismatch,
        }


@dataclass
class TypeReport:
    inferences: List[TypeInference] = field(default_factory=list)

    @property
    def mismatches(self) -> List[TypeInference]:
        return [i for i in self.inferences if i.mismatch]

    @property
    def any_mismatches(self) -> bool:
        return bool(self.mismatches)

    def summary(self) -> str:
        if not self.any_mismatches:
            return "All types match expectations."
        lines = [f"{len(self.mismatches)} type mismatch(es) found:"]
        for m in self.mismatches:
            lines.append(
                f"  {m.key}: inferred={m.inferred_type}, expected={m.expected_type}"
            )
        return "\n".join(lines)


def infer_type(value: str) -> str:
    if value == "":
        return "empty"
    if _BOOL_TRUE.match(value) or _BOOL_FALSE.match(value):
        return "bool"
    if _INT.match(value):
        return "int"
    if _FLOAT.match(value):
        return "float"
    if _URL.match(value):
        return "url"
    if _EMAIL.match(value):
        return "email"
    if _PATH.match(value):
        return "path"
    return "string"


def analyze_snapshot(
    env: Dict[str, str],
    expected: Optional[Dict[str, str]] = None,
) -> TypeReport:
    """Infer types for all keys; optionally compare against expected types."""
    expected = expected or {}
    inferences: List[TypeInference] = []
    for key, value in sorted(env.items()):
        inferred = infer_type(value)
        exp = expected.get(key)
        mismatch = exp is not None and inferred != exp
        inferences.append(
            TypeInference(
                key=key,
                value=value,
                inferred_type=inferred,
                expected_type=exp,
                mismatch=mismatch,
            )
        )
    return TypeReport(inferences=inferences)
