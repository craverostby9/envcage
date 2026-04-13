"""Tests for envcage.audit module."""

import json
import pytest
from pathlib import Path

from envcage.audit import record, load, clear, summary, AuditEntry


@pytest.fixture
def audit_file(tmp_path):
    return str(tmp_path / "test_audit.json")


def test_record_creates_entry(audit_file):
    entry = record("snapshot", {"name": "prod"}, audit_path=audit_file)
    assert entry.action == "snapshot"
    assert entry.details == {"name": "prod"}
    assert entry.timestamp


def test_record_persists_to_file(audit_file):
    record("snapshot", {"name": "prod"}, audit_path=audit_file)
    entries = load(audit_path=audit_file)
    assert len(entries) == 1
    assert entries[0].action == "snapshot"


def test_multiple_records_appended(audit_file):
    record("snapshot", {"name": "prod"}, audit_path=audit_file)
    record("validate", {"name": "prod", "passed": True}, audit_path=audit_file)
    record("diff", {"a": "snap1", "b": "snap2"}, audit_path=audit_file)
    entries = load(audit_path=audit_file)
    assert len(entries) == 3
    assert entries[1].action == "validate"


def test_load_returns_empty_list_when_no_file(audit_file):
    entries = load(audit_path=audit_file)
    assert entries == []


def test_clear_removes_file(audit_file):
    record("snapshot", audit_path=audit_file)
    clear(audit_path=audit_file)
    assert not Path(audit_file).exists()


def test_clear_on_missing_file_does_not_raise(audit_file):
    clear(audit_path=audit_file)  # should not raise


def test_audit_file_is_valid_json(audit_file):
    record("snapshot", {"name": "staging"}, audit_path=audit_file)
    content = Path(audit_file).read_text()
    data = json.loads(content)
    assert isinstance(data, list)
    assert data[0]["action"] == "snapshot"


def test_summary_no_entries(audit_file):
    result = summary(audit_path=audit_file)
    assert "No audit entries" in result


def test_summary_with_entries(audit_file):
    record("snapshot", {"name": "prod"}, audit_path=audit_file)
    record("diff", {"a": "snap1", "b": "snap2"}, audit_path=audit_file)
    result = summary(audit_path=audit_file)
    assert "2 entries" in result
    assert "snapshot" in result
    assert "diff" in result


def test_audit_entry_roundtrip():
    entry = AuditEntry(timestamp="2024-01-01T00:00:00+00:00", action="validate", details={"ok": True})
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.action == entry.action
    assert restored.details == entry.details
    assert restored.timestamp == entry.timestamp
