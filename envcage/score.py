"""Score a snapshot for environment hygiene quality."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from envcage.redact import is_sensitive, redacted_keys


@dataclass
class ScoreReport:
    total_keys: int = 0
    sensitive_keys: int = 0
    empty_values: int = 0
    long_values: int = 0
    suspicious_keys: int = 0
    penalties: list[str] = field(default_factory=list)
    score: int = 100


_SUSPICIOUS_PATTERNS = ("test", "debug", "dummy", "example", "changeme", "todo")
_LONG_VALUE_THRESHOLD = 512


def _apply_penalty(report: ScoreReport, points: int, reason: str) -> None:
    report.score = max(0, report.score - points)
    report.penalties.append(reason)


def score_snapshot(
    snapshot: dict[str, Any],
    *,
    penalise_empty: int = 5,
    penalise_long: int = 3,
    penalise_suspicious: int = 10,
    penalise_no_sensitive: int = 15,
) -> ScoreReport:
    """Return a ScoreReport for the given snapshot dict."""
    env: dict[str, str] = snapshot.get("env", {})
    report = ScoreReport(total_keys=len(env))

    sensitive = redacted_keys(env)
    report.sensitive_keys = len(sensitive)

    for key, value in env.items():
        str_value = str(value)

        if str_value.strip() == "":
            report.empty_values += 1
            _apply_penalty(report, penalise_empty, f"empty value for key '{key}'")

        if len(str_value) > _LONG_VALUE_THRESHOLD:
            report.long_values += 1
            _apply_penalty(
                report, penalise_long, f"unusually long value for key '{key}'"
            )

        lower_key = key.lower()
        if any(pat in lower_key for pat in _SUSPICIOUS_PATTERNS):
            report.suspicious_keys += 1
            _apply_penalty(
                report,
                penalise_suspicious,
                f"suspicious key name '{key}' (looks like placeholder)",
            )

    if report.total_keys > 0 and report.sensitive_keys == 0:
        _apply_penalty(
            report,
            penalise_no_sensitive,
            "no sensitive keys detected — snapshot may be incomplete",
        )

    return report


def summary(report: ScoreReport) -> str:
    """Return a human-readable summary of the score report."""
    lines = [
        f"Score : {report.score}/100",
        f"Keys  : {report.total_keys} total, {report.sensitive_keys} sensitive",
        f"Issues: {len(report.penalties)}",
    ]
    for penalty in report.penalties:
        lines.append(f"  - {penalty}")
    return "\n".join(lines)
