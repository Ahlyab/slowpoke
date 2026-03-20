from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

from slowpoke.execution.command_model import CommandPlan

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StepResult:
    command: str
    returncode: int
    stdout: str
    stderr: str


def execute_plan(plan: CommandPlan, *, auto_sudo: bool) -> list[StepResult]:
    results: list[StepResult] = []
    for step in plan.steps:
        args: list[str] = []
        if step.needs_sudo and auto_sudo:
            args.append("sudo")
        args.append(step.executable)
        args.extend(step.args)
        logger.info("Executing: %s", " ".join(args))
        cp = subprocess.run(args, capture_output=True, text=True, check=False, shell=False)
        result = StepResult(
            command=" ".join(args),
            returncode=cp.returncode,
            stdout=cp.stdout,
            stderr=cp.stderr,
        )
        results.append(result)
        if cp.returncode != 0:
            raise RuntimeError(f"Command failed: {result.command}\n{result.stderr}")
    return results
