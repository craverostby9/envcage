"""Tests for envcage.score."""
import pytest

from envcage.score import ScoreReport, score_snapshot, summary


@pytest.fixture()
def clean_snapshot() -> dict:
    return {
        "env": {
            "DATABASE_URL": "postgres://localhost/mydb",
            "SECRET_KEY": "s3cr3t-value",
            "APP_ENV": "production",
        }
    }


@pytest.fixture()
def empty_snapshot() -> dict:
    return {"env": {}}


def test_score_perfect_snapshot_is_100(clean_snapshot):
    report = score_snapshot(clean_snapshot)
    assert report.score == 100


def test_score_total_keys_counted(clean_snapshot):
    report = score_snapshot(clean_snapshot)
    assert report.total_keys == 3


def test_score_sensitive_keys_detected(clean_snapshot):
    report = score_snapshot(clean_snapshot)
    assert report.sensitive_keys >= 1


def test_score_empty_value_penalised():
    snap = {"env": {"SECRET_KEY": "real", "EMPTY_VAR": ""}}
    report = score_snapshot(snap, penalise_empty=5)
    assert report.empty_values == 1
    assert report.score <= 95
    assert any("empty value" in p for p in report.penalties)


def test_score_long_value_penalised():
    snap = {"env": {"SECRET_KEY": "x" * 600, "OTHER": "fine"}}
    report = score_snapshot(snap, penalise_long=3)
    assert report.long_values == 1
    assert report.score <= 97
    assert any("long value" in p for p in report.penalties)


def test_score_suspicious_key_penalised():
    snap = {"env": {"SECRET_KEY": "real", "DEBUG_TOKEN": "abc"}}
    report = score_snapshot(snap, penalise_suspicious=10)
    assert report.suspicious_keys >= 1
    assert any("suspicious" in p for p in report.penalties)


def test_score_no_sensitive_keys_penalised():
    snap = {"env": {"APP_ENV": "production", "PORT": "8080"}}
    report = score_snapshot(snap, penalise_no_sensitive=15)
    assert report.sensitive_keys == 0
    assert report.score <= 85
    assert any("no sensitive" in p for p in report.penalties)


def test_score_empty_snapshot_returns_100():
    snap = {"env": {}}
    report = score_snapshot(snap)
    assert report.score == 100
    assert report.total_keys == 0


def test_score_cannot_go_below_zero():
    snap = {
        "env": {
            "DEBUG_DUMMY_TEST": "",
            "EXAMPLE_TODO": "x" * 600,
        }
    }
    report = score_snapshot(snap)
    assert report.score >= 0


def test_summary_contains_score(clean_snapshot):
    report = score_snapshot(clean_snapshot)
    text = summary(report)
    assert "Score" in text
    assert str(report.score) in text


def test_summary_lists_penalties():
    snap = {"env": {"SECRET_KEY": "real", "EMPTY_VAR": ""}}
    report = score_snapshot(snap)
    text = summary(report)
    assert "empty value" in text


def test_multiple_penalties_accumulate():
    snap = {
        "env": {
            "SECRET_KEY": "s3cr3t",
            "DEBUG_VAR": "",
            "TEST_TOKEN": "x" * 600,
        }
    }
    report = score_snapshot(snap)
    assert len(report.penalties) >= 2
