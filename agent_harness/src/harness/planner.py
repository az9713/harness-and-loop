from __future__ import annotations

from abc import ABC, abstractmethod

from .context import WorkingContext
from .types import Action, RunState


class Planner(ABC):
    @abstractmethod
    def plan_next(self, state: RunState, context: WorkingContext) -> Action:
        raise NotImplementedError


class RuleBasedPlanner(Planner):
    """Local planner used for smoke tests before an LLM client is wired in."""

    def plan_next(self, state: RunState, context: WorkingContext) -> Action:
        called = [obs.name for obs in state.observations]
        if "retrieve_memory" not in called:
            return Action(kind="tool", name="retrieve_memory", args={"query": state.task, "k": 5})
        if "read_blueprint_sources" not in called:
            return Action(kind="tool", name="read_blueprint_sources", args={"max_chars": 1600})
        if "make_build_plan" not in called:
            return Action(kind="tool", name="make_build_plan", args={"task": state.task})
        return Action(kind="final", final=self._final_answer(state))

    def _final_answer(self, state: RunState) -> str:
        plan_items: list[str] = []
        memory_count = 0
        source_count = 0
        for obs in state.observations:
            if obs.name == "retrieve_memory":
                memory_count = len(obs.data.get("hits", []))
            if obs.name == "read_blueprint_sources":
                source_count = len(obs.data.get("snippets", {}))
            if obs.name == "make_build_plan":
                plan_items = list(obs.data.get("plan", []))

        bullets = "\n".join(f"- {item}" for item in plan_items)
        return (
            "Built a blueprint-aligned harness design using the local source pack.\n\n"
            f"Retrieved {memory_count} memory hits and read {source_count} text blueprint sources.\n\n"
            "Harness components:\n"
            "- Procedural memory: skill files and operating rules.\n"
            "- Semantic memory: durable facts about harness, loop engineering, and LLM Ops.\n"
            "- Episodic memory: dated workspace events and generated artifacts.\n"
            "- Tools: allow-listed functions for retrieval, source reading, and build planning.\n"
            "- Guardrails: max iterations, tool permissions, irreversible-action block, and final-answer checks.\n"
            "- Trace: every planner decision, tool call, observation, and final answer is written as JSONL.\n"
            "- Eval: deterministic checks inspect the final answer and trajectory.\n"
            "- Gate: release is allowed only when evals pass and the run stays within loop budget.\n\n"
            "Execution plan:\n"
            f"{bullets}"
        )

