from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CommandStep:
    executable: str
    args: list[str] = field(default_factory=list)
    needs_sudo: bool = False
    rationale: str = ""

    def render(self, auto_sudo: bool) -> str:
        parts: list[str] = []
        if self.needs_sudo and auto_sudo:
            parts.append("sudo")
        parts.append(self.executable)
        parts.extend(self.args)
        return " ".join(parts)


@dataclass(frozen=True)
class CommandPlan:
    source: str
    reason: str
    steps: list[CommandStep]

    def is_empty(self) -> bool:
        return len(self.steps) == 0
