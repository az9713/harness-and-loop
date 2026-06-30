from __future__ import annotations

from pathlib import Path
from typing import Callable

from .memory import MemoryStore
from .types import ToolResult


class ToolRegistry:
    def __init__(self, memory: MemoryStore, workspace_root: Path) -> None:
        self.memory = memory
        self.workspace_root = workspace_root
        self._tools: dict[str, Callable[..., ToolResult]] = {
            "retrieve_memory": self.retrieve_memory,
            "read_blueprint_sources": self.read_blueprint_sources,
            "make_build_plan": self.make_build_plan,
        }

    def call(self, name: str, **kwargs: object) -> ToolResult:
        tool = self._tools.get(name)
        if not tool:
            return ToolResult(name=name, ok=False, data={}, error=f"unknown tool: {name}")
        return tool(**kwargs)

    def retrieve_memory(self, query: object = "", k: object = 5) -> ToolResult:
        hits = self.memory.search(str(query), int(k))
        return ToolResult(
            name="retrieve_memory",
            ok=True,
            data={"hits": [hit.__dict__ for hit in hits]},
        )

    def read_blueprint_sources(self, max_chars: object = 1800) -> ToolResult:
        limit = int(max_chars)
        source_names = ["transcript.txt", "gpt5.5_summary.txt"]
        snippets: dict[str, str] = {}
        for name in source_names:
            path = self.workspace_root / name
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="replace")
                snippets[name] = text[:limit]
        image_exists = (self.workspace_root / "harness_llm_ops.png").exists()
        return ToolResult(
            name="read_blueprint_sources",
            ok=True,
            data={"snippets": snippets, "diagram_available": image_exists},
        )

    def make_build_plan(self, task: object = "") -> ToolResult:
        plan = [
            "Load procedural memory from skill files and operating rules.",
            "Retrieve semantic facts and episodic events relevant to the task.",
            "Assemble a bounded working context for the planner/model.",
            "Let the planner propose tool or final-answer actions.",
            "Authorize tools through an allow-list and approval policy.",
            "Run a max-iteration loop with no-progress and blocked-state guardrails.",
            "Trace context, planner decisions, tool calls, observations, and final output.",
            "Evaluate the full trajectory and gate release on deterministic checks.",
        ]
        return ToolResult(name="make_build_plan", ok=True, data={"task": str(task), "plan": plan})

