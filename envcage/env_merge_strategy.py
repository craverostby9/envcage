"""Merge strategies for combining environment snapshots."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

STRATEGY_LAST_WINS = "last_wins"
STRATEGY_FIRST_WINS = "first_wins"
STRATEGY_STRICT = "strict"


@dataclass
class StrategyResult:
    env: Dict[str, str]
    conflicts: Dict[str, List[str]] = field(default_factory=dict)
    strategy: str = STRATEGY_LAST_WINS

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def summary(self) -> str:
        lines = [f"Strategy : {self.strategy}", f"Keys     : {len(self.env)}"]
        if self.conflicts:
            lines.append(f"Conflicts: {len(self.conflicts)}")
            for key, vals in self.conflicts.items():
                lines.append(f"  {key}: {vals}")
        return "\n".join(lines)


def apply_strategy(
    snapshots: List[Dict[str, str]],
    strategy: str = STRATEGY_LAST_WINS,
) -> StrategyResult:
    if not snapshots:
        return StrategyResult(env={}, strategy=strategy)

    conflicts: Dict[str, List[str]] = {}
    env: Dict[str, str] = {}

    if strategy == STRATEGY_FIRST_WINS:
        for snap in snapshots:
            for k, v in snap.items():
                if k not in env:
                    env[k] = v
                elif env[k] != v:
                    conflicts.setdefault(k, [env[k]])
                    if v not in conflicts[k]:
                        conflicts[k].append(v)
        return StrategyResult(env=env, conflicts=conflicts, strategy=strategy)

    if strategy == STRATEGY_STRICT:
        base = snapshots[0].copy()
        for snap in snapshots[1:]:
            for k, v in snap.items():
                if k in base and base[k] != v:
                    conflicts.setdefault(k, [base[k]])
                    if v not in conflicts[k]:
                        conflicts[k].append(v)
                else:
                    base[k] = v
        return StrategyResult(env=base, conflicts=conflicts, strategy=strategy)

    # default: last_wins
    for snap in snapshots:
        for k, v in snap.items():
            if k in env and env[k] != v:
                conflicts.setdefault(k, [env[k]])
                if v not in conflicts[k]:
                    conflicts[k].append(v)
            env[k] = v
    return StrategyResult(env=env, conflicts=conflicts, strategy=strategy)
