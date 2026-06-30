# Agent Harness MVP

This is a local, dependency-free implementation of the harness/LLM Ops blueprint in `harness_llm_ops_notes.html`.

It is intentionally small but complete:

- **Harness runtime:** context assembly, memory retrieval, tool loop, permissions, stop rules.
- **Memory:** procedural skill files, semantic facts, episodic events.
- **LLM Ops:** trace recording, deterministic evals, and a release gate.
- **Model seam:** a `Planner` interface with a rule-based local planner. Replace it with an LLM client later without changing the harness shell.

## Run

From this folder:

```powershell
python run_harness.py "Build me a harness based on the blueprint"
```

Or from the workspace root:

```powershell
python agent_harness/run_harness.py "Build me a harness based on the blueprint"
```

The run writes JSONL traces to:

```text
agent_harness/traces/runs.jsonl
```

## Mental Model

The harness owns the deterministic boundaries:

```text
task -> context assembler -> planner -> permissioned tools -> guardrails -> final answer
                                      |
                                      v
                                trace -> eval -> release gate
```

The model proposes actions. The harness authorizes actions, executes tools, records events, evaluates the trajectory, and decides whether a run is releasable.

## Swap In A Real LLM

Implement the `Planner.plan_next(...)` method in `src/harness/planner.py` with a real model call. Keep the same action contract:

```python
Action(kind="tool", name="retrieve_memory", args={"query": "...", "k": 4})
Action(kind="final", final="...")
```

The surrounding harness remains unchanged.

