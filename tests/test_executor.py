from __future__ import annotations

import subprocess

import pytest

from slowpoke.execution.command_model import CommandPlan, CommandStep
from slowpoke.execution.executor import execute_plan


def test_execute_plan_success(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    plan = CommandPlan(
        source="test",
        reason="ok",
        steps=[CommandStep(executable="apt-get", args=["install", "-y", "curl"], needs_sudo=True)],
    )
    results = execute_plan(plan, auto_sudo=True)
    assert len(results) == 1
    assert results[0].returncode == 0


def test_execute_plan_raises_on_failure(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=1, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)
    plan = CommandPlan(
        source="test",
        reason="fail",
        steps=[CommandStep(executable="apt-get", args=["install", "-y", "missing"], needs_sudo=True)],
    )
    with pytest.raises(RuntimeError):
        execute_plan(plan, auto_sudo=True)
