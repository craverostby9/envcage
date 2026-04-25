"""Persist and load expected-type schemas for snapshot keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envcage.env_variable_type import analyze_snapshot, infer_type, INFERRED_TYPES


TypeSchema = Dict[str, str]  # key -> expected type


def create_schema(
    keys: list,
    defaults: Optional[TypeSchema] = None,
) -> TypeSchema:
    """Create a type schema for the given keys with optional default type mappings."""
    schema: TypeSchema = {}
    defaults = defaults or {}
    for key in sorted(set(keys)):
        schema[key] = defaults.get(key, "string")
    return schema


def schema_from_snapshot(env: Dict[str, str]) -> TypeSchema:
    """Derive a type schema by inferring types from an existing snapshot."""
    report = analyze_snapshot(env)
    return {inf.key: inf.inferred_type for inf in report.inferences}


def save_schema(schema: TypeSchema, path: str) -> None:
    """Persist a type schema to a JSON file."""
    Path(path).write_text(json.dumps(schema, indent=2, sort_keys=True))


def load_schema(path: str) -> TypeSchema:
    """Load a type schema from a JSON file."""
    return json.loads(Path(path).read_text())


def validate_schema(schema: TypeSchema) -> list:
    """Return a list of error strings for any invalid type names in the schema."""
    errors = []
    for key, type_name in schema.items():
        if type_name not in INFERRED_TYPES:
            errors.append(
                f"Key '{key}' has unknown type '{type_name}'. "
                f"Valid types: {', '.join(INFERRED_TYPES)}"
            )
    return errors
