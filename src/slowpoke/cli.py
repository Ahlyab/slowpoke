from __future__ import annotations

import argparse

from slowpoke.core.config import load_settings
from slowpoke.core.logging import configure_logging
from slowpoke.core.orchestrator import build_install_plan, build_llm_client, build_search_client
from slowpoke.execution.executor import execute_plan
from slowpoke.system.system_info import create_package_manager, detect_linux_system


def _confirm(prompt: str) -> bool:
    value = input(f"{prompt} [y/N]: ").strip().lower()
    return value in {"y", "yes"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Slowpoke Linux package installer")
    parser.add_argument("app_name", nargs="?", help="Application/package to install")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm execution after dry-run")
    args = parser.parse_args()

    settings = load_settings()
    configure_logging(settings.log_level, settings.log_file)

    info = detect_linux_system()
    pm = create_package_manager(info.package_manager)
    llm = build_llm_client(settings)
    search_client = build_search_client(settings)

    app_name = args.app_name or input("Which package/app do you want to install? ").strip()
    if not app_name:
        print("No package requested. Exiting.")
        return 1

    plan = build_install_plan(
        llm=llm,
        package_manager=pm,
        package_query=app_name,
        search_client=search_client,
    )

    print(f"Detected distro: {info.pretty_name}")
    print(f"Detected package manager: {info.package_manager}")
    print("\nDry-run plan:")
    for idx, step in enumerate(plan.steps, start=1):
        print(f"{idx}. {step.render(auto_sudo=settings.auto_sudo)}")
        if step.rationale:
            print(f"   reason: {step.rationale}")

    if not args.yes and not _confirm("Execute these commands?"):
        print("Cancelled by user.")
        return 0

    execute_plan(plan, auto_sudo=settings.auto_sudo)
    print("Installation workflow completed successfully.")
    return 0
