from __future__ import annotations

from typing import Any

from .config import HarnessConfig
from .types import RunState


class ReleaseGate:
    def __init__(self, config: HarnessConfig) -> None:
        self.config = config

    def decide(self, state: RunState, eval_result: dict[str, Any]) -> dict[str, Any]:
        reasons: list[str] = []
        if not eval_result.get("passed"):
            reasons.append("eval failed")
        if state.iteration > self.config.max_iterations:
            reasons.append("loop budget exceeded")
        if state.blocked_reason:
            reasons.append(state.blocked_reason)
        return {
            "release_allowed": not reasons,
            "reasons": reasons,
        }

