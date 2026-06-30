# Harness Builder Skill

Use this skill when the task is to design, implement, or explain an AI agent harness.

Required structure:

1. Define the runtime boundary: task, context, planner/model, tools, loop, final answer.
2. Split memory into procedural, semantic, and episodic stores.
3. Put every tool behind permission checks.
4. Add loop guardrails: max iterations, stop condition, blocked state, and approval boundary.
5. Trace every run as an event tree.
6. Evaluate the trajectory, not only the final answer.
7. Gate prompt/config/tool/RAG changes before release.

Design rule:

Let the model think probabilistically; make the harness act deterministically.

