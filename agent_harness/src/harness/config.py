from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HarnessConfig:
    root: Path
    max_iterations: int = 5
    allowed_tools: tuple[str, ...] = (
        "retrieve_memory",
        "read_blueprint_sources",
        "make_build_plan",
    )

    @property
    def system_prompt_path(self) -> Path:
        return self.root / "ai" / "system_prompt.md"

    @property
    def acceptance_path(self) -> Path:
        return self.root / "ai" / "acceptance_criteria.md"

    @property
    def skills_dir(self) -> Path:
        return self.root / "skills"

    @property
    def semantic_path(self) -> Path:
        return self.root / "memory" / "semantic.jsonl"

    @property
    def episodic_path(self) -> Path:
        return self.root / "memory" / "episodic.jsonl"

    @property
    def evals_path(self) -> Path:
        return self.root / "evals" / "golden_cases.jsonl"

    @property
    def trace_path(self) -> Path:
        return self.root / "traces" / "runs.jsonl"

    @property
    def workspace_root(self) -> Path:
        return self.root.parent

