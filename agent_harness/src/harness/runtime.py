from __future__ import annotations

import uuid
from dataclasses import asdict
from pathlib import Path

from .config import HarnessConfig
from .context import ContextAssembler
from .evaluator import Evaluator
from .memory import MemoryStore
from .permissions import PermissionPolicy
from .planner import Planner, RuleBasedPlanner
from .release_gate import ReleaseGate
from .tools import ToolRegistry
from .tracing import TraceRecorder
from .types import RunState, ToolResult


class HarnessRuntime:
    def __init__(self, root: Path, planner: Planner | None = None) -> None:
        self.config = HarnessConfig(root=root)
        self.memory = MemoryStore(
            semantic_path=self.config.semantic_path,
            episodic_path=self.config.episodic_path,
            skills_dir=self.config.skills_dir,
        )
        self.context = ContextAssembler(self.config)
        self.permissions = PermissionPolicy(self.config)
        self.tools = ToolRegistry(self.memory, self.config.workspace_root)
        self.planner = planner or RuleBasedPlanner()
        self.evaluator = Evaluator(self.config)
        self.release_gate = ReleaseGate(self.config)

    def run(self, task: str) -> dict[str, object]:
        run_id = str(uuid.uuid4())
        state = RunState(task=task, run_id=run_id)
        trace = TraceRecorder(self.config, run_id)
        trace.record("run_started", task=task)

        while state.iteration < self.config.max_iterations:
            state.iteration += 1
            memory_hits = self.memory.search(task, k=5)
            observations = [self._observation_summary(obs) for obs in state.observations]
            working_context = self.context.assemble(task, memory_hits, observations)
            trace.record("context_assembled", prompt_chars=len(working_context.as_prompt()), memory_hits=len(memory_hits))

            action = self.planner.plan_next(state, working_context)
            trace.record_action(action)

            if action.kind == "final":
                state.final_answer = action.final
                trace.record("final_answer", chars=len(state.final_answer))
                break

            allowed, reason = self.permissions.authorize(action)
            trace.record("permission_check", action=asdict(action), allowed=allowed, reason=reason)
            if not allowed:
                state.blocked_reason = reason
                break

            result = self.tools.call(action.name, **action.args)
            state.observations.append(result)
            trace.record_tool_result(result)
            if not result.ok:
                state.blocked_reason = result.error
                break

        if not state.final_answer and not state.blocked_reason:
            state.blocked_reason = "loop budget exhausted before final answer"

        eval_result = self.evaluator.evaluate(state)
        gate_result = self.release_gate.decide(state, eval_result)
        trace.flush(state.final_answer, eval_result, gate_result)

        return {
            "run_id": run_id,
            "final_answer": state.final_answer,
            "blocked_reason": state.blocked_reason,
            "iterations": state.iteration,
            "eval": eval_result,
            "gate": gate_result,
            "trace_path": str(self.config.trace_path),
        }

    def _observation_summary(self, result: ToolResult) -> str:
        if result.ok:
            return f"{result.name}: {result.data}"
        return f"{result.name}: ERROR {result.error}"

