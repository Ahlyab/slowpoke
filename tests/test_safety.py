from __future__ import annotations

import pytest

from slowpoke.execution.command_model import CommandPlan, CommandStep
from slowpoke.execution.safety import validate_plan


def test_validate_plan_accepts_safe_command():
    plan = CommandPlan(
        source="test",
        reason="safe",
        steps=[CommandStep(executable="apt-get", args=["install", "-y", "curl"], needs_sudo=True)],
    )
    validate_plan(plan)


def test_validate_plan_rejects_metacharacters():
    plan = CommandPlan(
        source="test",
        reason="bad",
        steps=[CommandStep(executable="apt-get", args=["install", "curl;rm"], needs_sudo=True)],
    )
    with pytest.raises(ValueError):
        validate_plan(plan)
