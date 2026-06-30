# Acceptance Criteria

A run is releasable when:

- The final answer is non-empty and directly addresses the task.
- The trace includes context assembly, at least one planner decision, and a final answer.
- Tool calls are authorized by the permission layer.
- Loop iterations stay within budget.
- The answer references the harness blueprint concepts: memory, tools, guardrails, trace, eval, and gate.
- No irreversible tool action is taken without approval.

