from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .jsonl import read_jsonl


TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


@dataclass(frozen=True)
class MemoryHit:
    source: str
    id: str
    text: str
    score: int


class MemoryStore:
    def __init__(self, semantic_path: Path, episodic_path: Path, skills_dir: Path) -> None:
        self.semantic_rows = read_jsonl(semantic_path)
        self.episodic_rows = read_jsonl(episodic_path)
        self.skill_rows = self._load_skills(skills_dir)

    def search(self, query: str, k: int = 5) -> list[MemoryHit]:
        query_tokens = tokens(query)
        candidates: list[MemoryHit] = []
        for source, rows in (
            ("procedural", self.skill_rows),
            ("semantic", self.semantic_rows),
            ("episodic", self.episodic_rows),
        ):
            for row in rows:
                text = str(row.get("text", ""))
                score = len(query_tokens & tokens(text))
                if score:
                    candidates.append(MemoryHit(source, str(row.get("id", "")), text, score))
        return sorted(candidates, key=lambda hit: (-hit.score, hit.source, hit.id))[:k]

    def _load_skills(self, skills_dir: Path) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        if not skills_dir.exists():
            return rows
        for skill in skills_dir.rglob("SKILL.md"):
            rows.append({
                "id": str(skill.relative_to(skills_dir)),
                "text": skill.read_text(encoding="utf-8"),
            })
        return rows

