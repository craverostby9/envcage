"""Integration helpers for policy enforcement within the envcage CLI pipeline.

Provides convenience functions that combine policy checking with auditing
and linting, suitable for use in pre-commit hooks or CI pipelines.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from envcage.policy import Policy, enforce_policy, load_policy, enforce_policy_file, PolicyResult
from envcage.snapshot import load
from envcage.audit import record as audit_record


def check_all_snapshots(
    policy_path: str,
    snapshot_paths: List[str],
    audit_path: Optional[str] = None,
) -> Dict[str, PolicyResult]:
    """Enforce a policy against multiple snapshot files.

    Returns a mapping of snapshot path -> PolicyResult.
    Optionally records each result to the audit log.
    """
    results: Dict[str, PolicyResult] = {}
    for snap_path in snapshot_paths:
        result = enforce_policy_file(policy_path, snap_path)
        results[snap_path] = result
        if audit_path:
            status = "pass" if result.passed else "fail"
            audit_record(
                action=f"policy-check:{status}",
                snapshot=snap_path,
                detail=f"{len(result.violations)} violation(s)",
                path=audit_path,
            )
    return results


def any_policy_failures(results: Dict[str, PolicyResult]) -> bool:
    """Return True if any snapshot failed the policy check."""
    return any(not r.passed for r in results.values())


def batch_policy_summary(results: Dict[str, PolicyResult]) -> str:
    """Return a human-readable summary of batch policy check results."""
    lines: List[str] = []
    passed = sum(1 for r in results.values() if r.passed)
    failed = len(results) - passed
    lines.append(f"Policy check: {passed} passed, {failed} failed")
    for path, result in results.items():
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"  [{status}] {path}")
        for v in result.violations:
            lines.append(f"         - {v}")
    return "\n".join(lines)
