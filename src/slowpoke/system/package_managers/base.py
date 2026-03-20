from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from slowpoke.execution.command_model import CommandPlan, CommandStep


@dataclass(frozen=True)
class PackageCandidate:
    name: str
    summary: str


class PackageManager(ABC):
    name: str

    @abstractmethod
    def search(self, query: str) -> list[PackageCandidate]:
        raise NotImplementedError

    @abstractmethod
    def build_install_plan(self, package_name: str) -> CommandPlan:
        raise NotImplementedError

    @staticmethod
    def plan(source: str, reason: str, executable: str, args: list[str]) -> CommandPlan:
        return CommandPlan(
            source=source,
            reason=reason,
            steps=[CommandStep(executable=executable, args=args, needs_sudo=True)],
        )
