from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .config import HarnessConfig
from .jsonl import read_jsonl
from .types import RunState


class Evaluator:
    def __init__(self, config: HarnessConfig) -> None:
        self.config = config
        self.golden_cases = read_jsonl(config.evals_path)

    def evaluate(self, state: RunState) -> dict[str, Any]:
        final_lower = state.final_answer.lower()
        required_terms = self._required_terms(state.task)
        term_checks = {term: term.lower() in final_lower for term in required_terms}
        checks = {
            "final_answer_non_empty": bool(state.final_answer.strip()),
            "loop_within_budget": state.iteration <= self.config.max_iterations,
            "planner_decision_seen": state.iteration > 0,
            "tool_observation_seen": bool(state.observations),
            "required_terms_present": all(term_checks.values()),
            "no_blocked_reason": not state.blocked_reason,
        }
        return {
            "passed": all(checks.values()),
            "checks": checks,
            "required_terms": term_checks,
            "observations": [asdict(obs) for obs in state.observations],
        }

    def _required_terms(self, task: str) -> list[str]:
        task_lower = task.lower()
        for case in self.golden_cases:
            if case.get("task", "").lower() in task_lower or task_lower in case.get("task", "").lower():
                return list(case.get("required_terms", []))
        return ["memory", "tools", "guardrails", "trace", "eval", "gate"]

