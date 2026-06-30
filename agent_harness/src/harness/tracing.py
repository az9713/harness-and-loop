from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

from .config import HarnessConfig
from .jsonl import append_jsonl
from .types import Action, ToolResult


class TraceRecorder:
    def __init__(self, config: HarnessConfig, run_id: str) -> None:
        self.config = config
        self.run_id = run_id
        self.started_at = time.time()
        self.events: list[dict[str, Any]] = []

    def record(self, event_type: str, **payload: Any) -> None:
        self.events.append({
            "run_id": self.run_id,
            "t_ms": int((time.time() - self.started_at) * 1000),
            "event": event_type,
            "payload": payload,
        })

    def record_action(self, action: Action) -> None:
        self.record("planner_decision", action=asdict(action))

    def record_tool_result(self, result: ToolResult) -> None:
        self.record("tool_result", result=asdict(result))

    def flush(self, final_answer: str, eval_result: dict[str, Any], gate_result: dict[str, Any]) -> None:
        append_jsonl(self.config.trace_path, {
            "run_id": self.run_id,
            "duration_ms": int((time.time() - self.started_at) * 1000),
            "events": self.events,
            "final_answer": final_answer,
            "eval": eval_result,
            "gate": gate_result,
        })

