"""Tests for envcage.schema."""
import json
import pytest
from envcage.schema import (
    SchemaRule,
    SchemaReport,
    SchemaViolation,
    create_schema,
    save_schema,
    load_schema,
    validate_schema,
    validate_schema_file,
)


@pytest.fixture
def simple_env():
    return {"PORT": "8080", "ENV": "production", "SECRET_KEY": "abc123"}


@pytest.fixture
def basic_rules():
    return [
        SchemaRule(key="PORT", required=True, pattern=r"\d+"),
        SchemaRule(key="ENV", required=True, allowed_values=["production", "staging", "development"]),
        SchemaRule(key="SECRET_KEY", required=True, min_length=6),
    ]


def test_valid_env_passes(simple_env, basic_rules):
    report = validate_schema(simple_env, basic_rules)
    assert report.is_valid


def test_missing_required_key_is_violation(basic_rules):
    env = {"PORT": "8080"}  # ENV and SECRET_KEY missing
    report = validate_schema(env, basic_rules)
    assert not report.is_valid
    keys = [v.key for v in report.violations]
    assert "ENV" in keys
    assert "SECRET_KEY" in keys


def test_optional_key_missing_is_not_violation():
    rules = [SchemaRule(key="DEBUG", required=False)]
    report = validate_schema({}, rules)
    assert report.is_valid


def test_pattern_violation_detected():
    rules = [SchemaRule(key="PORT", pattern=r"\d+")]
    report = validate_schema({"PORT": "not-a-number"}, rules)
    assert not report.is_valid
    assert report.violations[0].key == "PORT"
    assert "pattern" in report.violations[0].message


def test_min_length_violation_detected():
    rules = [SchemaRule(key="SECRET_KEY", min_length=10)]
    report = validate_schema({"SECRET_KEY": "short"}, rules)
    assert not report.is_valid
    assert "too short" in report.violations[0].message


def test_max_length_violation_detected():
    rules = [SchemaRule(key="NAME", max_length=5)]
    report = validate_schema({"NAME": "toolongvalue"}, rules)
    assert not report.is_valid
    assert "too long" in report.violations[0].message


def test_allowed_values_violation_detected():
    rules = [SchemaRule(key="ENV", allowed_values=["staging", "production"])]
    report = validate_schema({"ENV": "local"}, rules)
    assert not report.is_valid
    assert "not in allowed values" in report.violations[0].message


def test_summary_on_valid_report():
    report = SchemaReport(violations=[])
    assert "passed" in report.summary()


def test_summary_on_invalid_report():
    report = SchemaReport(violations=[SchemaViolation("PORT", "required key is missing")])
    summary = report.summary()
    assert "PORT" in summary
    assert "violations" in summary


def test_save_and_load_schema(tmp_path, basic_rules):
    path = str(tmp_path / "schema.json")
    save_schema(basic_rules, path)
    loaded = load_schema(path)
    assert len(loaded) == len(basic_rules)
    assert loaded[0].key == basic_rules[0].key
    assert loaded[1].allowed_values == basic_rules[1].allowed_values


def test_schema_rule_round_trips():
    rule = SchemaRule(key="PORT", required=True, pattern=r"\d+", min_length=1, max_length=5, allowed_values=[])
    restored = SchemaRule.from_dict(rule.to_dict())
    assert restored.key == rule.key
    assert restored.pattern == rule.pattern
    assert restored.min_length == rule.min_length


def test_validate_schema_file(tmp_path):
    from envcage.snapshot import save, capture
    snap = capture(env={"PORT": "9000", "ENV": "staging"})
    snap_path = str(tmp_path / "snap.json")
    save(snap, snap_path)

    rules = [SchemaRule(key="PORT", pattern=r"\d+"), SchemaRule(key="ENV", required=True)]
    schema_path = str(tmp_path / "schema.json")
    save_schema(rules, schema_path)

    report = validate_schema_file(snap_path, schema_path)
    assert report.is_valid
