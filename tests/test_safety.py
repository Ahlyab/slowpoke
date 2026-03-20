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


def test_validate_plan_accepts_rpm_import_https():
    plan = CommandPlan(
        source="test",
        reason="rpm import",
        steps=[
            CommandStep(
                executable="rpm",
                args=["--import", "https://packages.microsoft.com/keys/microsoft.asc"],
                needs_sudo=True,
            )
        ],
    )
    validate_plan(plan)


def test_validate_plan_rejects_non_import_rpm_command():
    plan = CommandPlan(
        source="test",
        reason="unsafe rpm",
        steps=[CommandStep(executable="rpm", args=["-i", "pkg.rpm"], needs_sudo=True)],
    )
    with pytest.raises(ValueError):
        validate_plan(plan)
