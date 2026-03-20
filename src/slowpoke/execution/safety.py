from __future__ import annotations

from slowpoke.execution.command_model import CommandPlan

ALLOWED_EXECUTABLES = {
    "apt-get",
    "apt",
    "dnf",
    "pacman",
    "zypper",
    "apk",
    "flatpak",
    "curl",
    "wget",
    "tar",
    "make",
    "cmake",
    "pip",
    "pip3",
    "python",
    "python3",
    "rpm",
}

DENY_TOKENS = {
    "rm",
    "mkfs",
    "dd",
    ":(){:|:&};:",
    "shutdown",
    "reboot",
}


def validate_plan(plan: CommandPlan) -> None:
    if plan.is_empty():
        raise ValueError("Command plan is empty.")
    for step in plan.steps:
        if step.executable not in ALLOWED_EXECUTABLES:
            raise ValueError(f"Executable not allowed: {step.executable}")
        if step.executable == "rpm":
            if not step.args or step.args[0] != "--import" or len(step.args) != 2:
                raise ValueError("Only 'rpm --import <key>' is allowed.")
            key_source = step.args[1]
            if not (key_source.startswith("https://") or key_source.startswith("/")):
                raise ValueError("rpm --import source must be an https URL or absolute file path.")
        for token in [step.executable, *step.args]:
            if token in DENY_TOKENS:
                raise ValueError(f"Dangerous token in plan: {token}")
            if any(ch in token for ch in ["|", ";", "&&", "`"]):
                raise ValueError(f"Shell metacharacter not allowed in token: {token}")
