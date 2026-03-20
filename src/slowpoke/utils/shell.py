from __future__ import annotations

import subprocess


def run_capture(args: list[str], timeout_s: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=False,
        shell=False,
        text=True,
        capture_output=True,
        timeout=timeout_s,
    )
