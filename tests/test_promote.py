"""Tests for envcage.promote."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envcage.promote import (
    PromotionRecord,
    promote,
    load_log,
)
from envcage.snapshot import save


@pytest.fixture()
def snap_file(tmp_path: Path) -> str:
    path = str(tmp_path / "staging.json")
    save({"meta": {"captured_at": "2024-01-01T00:00:00+00:00"}, "env": {"APP": "hello", "PORT": "8080"}}, path)
    return path


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    return str(tmp_path / "promotions.json")


def test_promote_copies_snapshot(snap_file: str, tmp_path: Path, log_file: str) -> None:
    target = str(tmp_path / "production.json")
    promote(snap_file, target, "staging", "production", log_path=log_file)
    assert Path(target).exists()


def test_promote_target_contains_same_env(snap_file: str, tmp_path: Path, log_file: str) -> None:
    from envcage.snapshot import load

    target = str(tmp_path / "production.json")
    promote(snap_file, target, "staging", "production", log_path=log_file)
    data = load(target)
    assert data["env"]["APP"] == "hello"
    assert data["env"]["PORT"] == "8080"


def test_promote_returns_record(snap_file: str, tmp_path: Path, log_file: str) -> None:
    target = str(tmp_path / "production.json")
    record = promote(snap_file, target, "staging", "production", note="v1.2", log_path=log_file)
    assert isinstance(record, PromotionRecord)
    assert record.source_stage == "staging"
    assert record.target_stage == "production"
    assert record.note == "v1.2"


def test_promote_record_persisted(snap_file: str, tmp_path: Path, log_file: str) -> None:
    target = str(tmp_path / "production.json")
    promote(snap_file, target, "staging", "production", log_path=log_file)
    assert Path(log_file).exists()
    with open(log_file) as fh:
        records = json.load(fh)
    assert len(records) == 1
    assert records[0]["source_stage"] == "staging"
    assert records[0]["target_stage"] == "production"


def test_promote_multiple_records_appended(snap_file: str, tmp_path: Path, log_file: str) -> None:
    target1 = str(tmp_path / "prod1.json")
    target2 = str(tmp_path / "prod2.json")
    promote(snap_file, target1, "staging", "production", log_path=log_file)
    promote(snap_file, target2, "staging", "dr", log_path=log_file)
    records = load_log(log_file)
    assert len(records) == 2
    assert records[1].target_stage == "dr"


def test_load_log_empty_when_no_file(tmp_path: Path) -> None:
    records = load_log(str(tmp_path / "missing.json"))
    assert records == []


def test_promotion_record_round_trips() -> None:
    rec = PromotionRecord(
        source_stage="dev",
        target_stage="staging",
        source_file="dev.json",
        target_file="staging.json",
        note="nightly",
    )
    assert PromotionRecord.from_dict(rec.to_dict()).note == "nightly"
    assert PromotionRecord.from_dict(rec.to_dict()).source_stage == "dev"


def test_promote_record_has_timestamp(snap_file: str, tmp_path: Path, log_file: str) -> None:
    target = str(tmp_path / "production.json")
    record = promote(snap_file, target, "staging", "production", log_path=log_file)
    assert record.promoted_at  # non-empty ISO timestamp
