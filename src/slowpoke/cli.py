from __future__ import annotations

import argparse
import itertools
import sys
import threading
import time
from contextlib import contextmanager

from slowpoke.core.config import load_settings
from slowpoke.core.logging import configure_logging
from slowpoke.core.orchestrator import build_install_plan, build_llm_client, build_search_client
from slowpoke.execution.executor import execute_plan
from slowpoke.system.system_info import create_package_manager, detect_linux_system


def _confirm(prompt: str) -> bool:
    value = input(f"{prompt} [y/N]: ").strip().lower()
    return value in {"y", "yes"}


@contextmanager
def _spinner(message: str):
    if not sys.stdout.isatty():
        print(f"{message}...")
        yield
        return

    stop_event = threading.Event()

    def _run() -> None:
        for frame in itertools.cycle("|/-\\"):
            if stop_event.is_set():
                break
            print(f"\r{message} {frame}", end="", flush=True)
            time.sleep(0.1)

    worker = threading.Thread(target=_run, daemon=True)
    worker.start()
    try:
        yield
    except Exception:
        stop_event.set()
        worker.join(timeout=0.2)
        print(f"\r{message} failed.{' ' * 8}")
        raise
    finally:
        if not stop_event.is_set():
            stop_event.set()
            worker.join(timeout=0.2)
            print(f"\r{message} done.{' ' * 8}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Slowpoke Linux package installer")
    parser.add_argument("app_name", nargs="?", help="Application/package to install")
    parser.add_argument("--yes", action="store_true", help="Auto-confirm execution after dry-run")
    args = parser.parse_args()

    with _spinner("Loading configuration"):
        settings = load_settings()
        configure_logging(settings.log_level, settings.log_file, settings.dev_mode)

    with _spinner("Detecting Linux system"):
        info = detect_linux_system()
        pm = create_package_manager(info.package_manager)
    with _spinner("Initializing providers"):
        llm = build_llm_client(settings)
        search_client = build_search_client(settings)

    app_name = args.app_name or input("Which package/app do you want to install? ").strip()
    if not app_name:
        print("No package requested. Exiting.")
        return 1

    with _spinner(f"Building install plan for '{app_name}'"):
        plan = build_install_plan(
            llm=llm,
            package_manager=pm,
            package_query=app_name,
            search_client=search_client,
            distro_name=info.pretty_name,
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

    with _spinner("Executing plan"):
        execute_plan(plan, auto_sudo=settings.auto_sudo)
    print("Installation workflow completed successfully.")
    return 0
