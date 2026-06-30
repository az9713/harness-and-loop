# Agent Harness Onboarding

This guide explains how to use and extend `agent_harness/`. It is written for both users who want to run the harness and developers who want to modify it.

## What This Is

`agent_harness/` is a small, local implementation of the harness and LLM Ops blueprint from Sean's YouTube explainer on agent harnesses, loop engineering, evals, and LLM Ops.

The main idea is:

```text
The model proposes actions. The harness controls execution.
```

This repository currently uses a deterministic `RuleBasedPlanner` instead of a live LLM. That keeps the example dependency-free and easy to test while preserving the production-shaped boundaries: memory, context assembly, tools, permissions, loop guardrails, tracing, evals, and release gates.

## Requirements

Runtime requirements:

- Python 3.10 or newer recommended.
- No third-party Python packages are required.
- No API key is required.
- No OpenAI, Anthropic, LangChain, LangGraph, database, or vector store dependency is required for the current local version.

Optional tools:

- Git, if you want to commit changes.
- A shell such as PowerShell, Terminal, or bash.

## Quick Start For Users

From the repository root:

```powershell
python agent_harness/run_harness.py "Build me a harness based on the blueprint"
```

From inside `agent_harness/`:

```powershell
python run_harness.py "Build me a harness based on the blueprint"
```

If you omit the task, the CLI uses a default task:

```powershell
python agent_harness/run_harness.py
```

The command prints JSON with:

- `run_id`: unique ID for the run.
- `final_answer`: the harness output.
- `blocked_reason`: why the run stopped without a final answer, if applicable.
- `iterations`: loop count used by the runtime.
- `eval`: deterministic evaluation results.
- `gate`: release-gate decision.
- `trace_path`: where the JSONL trace was written.

## What To Expect

A successful run should:

1. Retrieve relevant procedural, semantic, and episodic memory.
2. Read local blueprint source snippets if available.
3. Generate a build plan.
4. Produce a final answer.
5. Evaluate the run.
6. Allow release if checks pass.
7. Append a trace to `agent_harness/traces/runs.jsonl`.

The trace file is intentionally simple JSONL. Each line is one run record containing the event sequence, final answer, eval result, and gate decision.

## Run Tests

From the repository root:

```powershell
python -m unittest discover agent_harness/tests
```

The test suite currently checks:

- A normal harness run passes evals and the release gate.
- An irreversible tool action is blocked unless explicitly approved.

## Directory Map

```text
agent_harness/
  README.md
  ONBOARDING.md
  run_harness.py

  ai/
    system_prompt.md
    acceptance_criteria.md

  skills/
    harness_builder/SKILL.md

  memory/
    semantic.jsonl
    episodic.jsonl

  evals/
    golden_cases.jsonl

  traces/
    runs.jsonl

  src/harness/
    __init__.py
    config.py
    context.py
    evaluator.py
    jsonl.py
    memory.py
    permissions.py
    planner.py
    release_gate.py
    runtime.py
    tools.py
    tracing.py
    types.py

  tests/
    test_harness.py
```

## Architecture Overview

The harness is organized around two loops.

The inner runtime loop:

```text
task
  -> memory search
  -> context assembly
  -> planner decision
  -> permission check
  -> tool call
  -> observation
  -> repeat or final answer
```

The outer LLM Ops loop:

```text
trace
  -> eval
  -> release gate
  -> allow or block release
```

The current implementation keeps both loops local and deterministic.

## Main Components

### `run_harness.py`

CLI entrypoint. It:

1. Reads the task from command-line arguments.
2. Constructs `HarnessRuntime` with `agent_harness/` as the root.
3. Runs the harness.
4. Prints the result as JSON.
5. Exits with code `1` if the release gate blocks the run.

### `src/harness/runtime.py`

The orchestrator. `HarnessRuntime` wires together:

- `HarnessConfig`
- `MemoryStore`
- `ContextAssembler`
- `PermissionPolicy`
- `ToolRegistry`
- `Planner`
- `Evaluator`
- `ReleaseGate`
- `TraceRecorder`

Its `run()` method owns the bounded agent loop. The default loop budget is five iterations.

### `src/harness/config.py`

Central configuration for paths and runtime limits.

Important defaults:

- `max_iterations = 5`
- allowed tools:
  - `retrieve_memory`
  - `read_blueprint_sources`
  - `make_build_plan`

### `src/harness/memory.py`

Loads and searches three memory classes:

- Procedural memory: `skills/**/SKILL.md`
- Semantic memory: `memory/semantic.jsonl`
- Episodic memory: `memory/episodic.jsonl`

Search is currently token-overlap based. It is deliberately simple, transparent, and dependency-free. A real system could replace this with embeddings, SQL, or hybrid retrieval.

### `src/harness/context.py`

Builds `WorkingContext` from:

- task
- system prompt
- acceptance criteria
- memory hits
- prior tool observations

`WorkingContext.as_prompt()` renders a prompt-shaped string. The rule-based planner does not need an actual prompt, but this preserves the seam needed for a real LLM planner.

### `src/harness/planner.py`

Defines the model seam.

`Planner` is an abstract interface:

```python
def plan_next(self, state: RunState, context: WorkingContext) -> Action:
    ...
```

`RuleBasedPlanner` is the local default. It follows a fixed sequence:

1. call `retrieve_memory`
2. call `read_blueprint_sources`
3. call `make_build_plan`
4. return a final answer

To use a real LLM, implement a new `Planner` subclass that returns the same `Action` objects.

### `src/harness/tools.py`

Defines the tool registry and built-in tools.

Current tools:

- `retrieve_memory`: searches procedural, semantic, and episodic memory.
- `read_blueprint_sources`: reads local `transcript.txt`, `gpt5.5_summary.txt`, and checks whether `harness_llm_ops.png` exists.
- `make_build_plan`: returns a structured plan for building a harness.

Note: the `.txt` files are not tracked in Git, but the tool can use them if they exist locally.

### `src/harness/permissions.py`

Authorizes tool actions before execution.

Current policy:

- non-tool actions are allowed
- tool name must be in the configured allow-list
- actions with `irreversible=True` are blocked unless you extend the policy

This is where production systems would add user approval, role-based access control, scopes, secrets policy, or external action review.

### `src/harness/tracing.py`

Records the run as an event sequence and appends the final run record to `traces/runs.jsonl`.

Recorded events include:

- run start
- context assembly
- planner decisions
- permission checks
- tool results
- final answer
- eval result
- gate result

### `src/harness/evaluator.py`

Runs deterministic evals over the completed trajectory.

Current checks:

- final answer is non-empty
- loop stayed within budget
- planner decision was seen
- tool observation was seen
- required terms are present
- no blocked reason exists

Required terms are loaded from `evals/golden_cases.jsonl` when the task matches a golden case. Otherwise, the evaluator falls back to a compact default rubric.

### `src/harness/release_gate.py`

Turns eval and runtime state into a release decision.

Release is blocked when:

- eval failed
- loop budget was exceeded
- the runtime has a blocked reason

### `src/harness/types.py`

Shared dataclasses:

- `Action`: planner output, either `tool` or `final`
- `ToolResult`: result from a tool call
- `RunState`: task state accumulated during the loop

## Data And Configuration Files

### `ai/system_prompt.md`

Local operating instructions for the agent. In a real LLM-backed planner, this would be part of the prompt context.

### `ai/acceptance_criteria.md`

Defines what a releasable run should satisfy.

### `skills/harness_builder/SKILL.md`

Procedural memory for harness-building tasks.

### `memory/semantic.jsonl`

Durable facts about harnesses, memory, loop engineering, and LLM Ops.

### `memory/episodic.jsonl`

Dated workspace events. This represents event memory rather than stable facts.

### `evals/golden_cases.jsonl`

Golden task definitions and required terms used by `Evaluator`.

### `traces/runs.jsonl`

Append-only local trace log. Running tests or the CLI may append new lines.

## Developer Workflow

1. Make your code or data change.
2. Run tests:

```powershell
python -m unittest discover agent_harness/tests
```

3. Optionally run the CLI manually:

```powershell
python agent_harness/run_harness.py "Build me a harness based on the blueprint"
```

4. Inspect the printed JSON and `agent_harness/traces/runs.jsonl`.
5. Commit only intentional changes. If a trace was produced only by local testing, decide whether to keep it as evidence or restore it before committing.

## Extending The Harness

### Add a new tool

1. Add a method to `ToolRegistry` in `src/harness/tools.py`.
2. Register it in `self._tools`.
3. Add the tool name to `HarnessConfig.allowed_tools`.
4. Add permission behavior in `PermissionPolicy` if the tool has risk.
5. Add tests for allowed and blocked paths.

### Add a new memory item

Add a JSONL row to the appropriate file:

- `memory/semantic.jsonl` for durable facts
- `memory/episodic.jsonl` for dated events
- `skills/**/SKILL.md` for procedural instructions

Keep one JSON object per line.

### Add or change evals

Edit `evals/golden_cases.jsonl` and update `Evaluator` if the check needs more than term matching.

For stronger evals, consider checking:

- whether the right tools were called
- whether unsafe tools were blocked
- whether the final answer cites the right observations
- whether loop count stayed under a tighter budget
- whether output matches a schema

### Wire in a real LLM

Create a new class that implements `Planner`:

```python
from harness.planner import Planner
from harness.types import Action, RunState
from harness.context import WorkingContext

class LlmPlanner(Planner):
    def plan_next(self, state: RunState, context: WorkingContext) -> Action:
        prompt = context.as_prompt()
        # call your model here
        # parse model output into an Action
        return Action(kind="final", final="...")
```

Then construct the runtime with your planner:

```python
runtime = HarnessRuntime(ROOT, planner=LlmPlanner())
```

If the new planner calls a hosted model, document the required package, environment variables, and API key. The current repository does not require any of those.

## API Keys And Secrets

Current state:

- No API keys are needed.
- No secrets are read.
- No network calls are made by the harness.

If you add a hosted LLM or external tool later:

- Do not hard-code secrets.
- Read secrets from environment variables or a secret manager.
- Add required variables to documentation.
- Add permission checks for tools that write, send, delete, charge money, or call external services.

## Known Limitations

This is an MVP harness, not a production agent framework.

Current limitations:

- Memory search is token overlap, not embeddings.
- The default planner is rule-based, not an LLM.
- Tool set is intentionally small.
- Trace storage is a local JSONL file.
- Eval logic is deterministic and simple.
- The release gate is binary and local.
- No concurrency, retries, model routing, streaming, or external observability backend is included.

These limitations are deliberate. The project is meant to show the boundaries and interfaces before adding heavier infrastructure.

## Troubleshooting

### `python` is not found

Install Python or use the Python launcher if available:

```powershell
py agent_harness/run_harness.py "Build me a harness based on the blueprint"
```

### The run exits with code `1`

The release gate blocked the run. Inspect the printed JSON:

- `blocked_reason`
- `eval.checks`
- `gate.reasons`

### The trace file changed after tests

The runtime appends trace records to `agent_harness/traces/runs.jsonl`. That is expected. Before committing, decide whether the new trace is useful evidence or just local test output.

### Blueprint text snippets are empty

`read_blueprint_sources` only reads `transcript.txt` and `gpt5.5_summary.txt` if they exist locally. Those `.txt` files are intentionally ignored by Git, so a fresh clone may not have them. The harness still runs without them.

## User Summary

If you only want to use the harness, run:

```powershell
python agent_harness/run_harness.py "your task here"
```

Read the JSON result and check whether `gate.release_allowed` is `true`.

## Developer Summary

If you want to develop the harness, start with these files:

- `src/harness/runtime.py` for control flow
- `src/harness/planner.py` for the model seam
- `src/harness/tools.py` for tool behavior
- `src/harness/permissions.py` for action authorization
- `src/harness/evaluator.py` and `src/harness/release_gate.py` for LLM Ops checks
