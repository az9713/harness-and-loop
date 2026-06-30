from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ActionKind = Literal["tool", "final"]


@dataclass(frozen=True)
class Action:
    kind: ActionKind
    name: str = ""
    args: dict[str, Any] = field(default_factory=dict)
    final: str = ""


@dataclass
class ToolResult:
    name: str
    ok: bool
    data: dict[str, Any]
    error: str = ""


@dataclass
class RunState:
    task: str
    run_id: str
    iteration: int = 0
    observations: list[ToolResult] = field(default_factory=list)
    final_answer: str = ""
    blocked_reason: str = ""

