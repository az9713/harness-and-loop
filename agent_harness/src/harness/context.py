from __future__ import annotations

from dataclasses import dataclass

from .config import HarnessConfig
from .memory import MemoryHit


@dataclass(frozen=True)
class WorkingContext:
    task: str
    system_prompt: str
    acceptance_criteria: str
    memory_hits: list[MemoryHit]
    observations: list[str]

    def as_prompt(self) -> str:
        memory = "\n".join(f"- [{hit.source}:{hit.id}] {hit.text}" for hit in self.memory_hits)
        observations = "\n".join(f"- {item}" for item in self.observations)
        return (
            f"System:\n{self.system_prompt}\n\n"
            f"Task:\n{self.task}\n\n"
            f"Relevant memory:\n{memory or '- none'}\n\n"
            f"Observations:\n{observations or '- none'}\n\n"
            f"Acceptance criteria:\n{self.acceptance_criteria}\n"
        )


class ContextAssembler:
    def __init__(self, config: HarnessConfig) -> None:
        self.config = config

    def assemble(self, task: str, memory_hits: list[MemoryHit], observations: list[str]) -> WorkingContext:
        return WorkingContext(
            task=task,
            system_prompt=self.config.system_prompt_path.read_text(encoding="utf-8"),
            acceptance_criteria=self.config.acceptance_path.read_text(encoding="utf-8"),
            memory_hits=memory_hits,
            observations=observations,
        )

