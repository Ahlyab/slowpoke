from __future__ import annotations

import subprocess


def run_capture(args: list[str], timeout_s: int = 20) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            args,
            check=False,
            shell=False,
            text=True,
            capture_output=True,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired as exc:
        # Keep callers simple: return a failed process result instead of raising.
        return subprocess.CompletedProcess(
            args=args,
            returncode=124,
            stdout=exc.stdout if isinstance(exc.stdout, str) else "",
            stderr=f"Command timed out after {timeout_s} seconds",
        )
