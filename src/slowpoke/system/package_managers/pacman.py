from __future__ import annotations

from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.utils.shell import run_capture


class PacmanManager(PackageManager):
    name = "pacman"

    def search(self, query: str) -> list[PackageCandidate]:
        cp = run_capture(["pacman", "-Ss", query])
        if cp.returncode != 0:
            return []
        candidates: list[PackageCandidate] = []
        lines = cp.stdout.splitlines()
        for i, line in enumerate(lines):
            if "/" in line and " " in line:
                parts = line.split()
                pkg = parts[0]
                summary = lines[i + 1].strip() if i + 1 < len(lines) else ""
                candidates.append(PackageCandidate(name=pkg.split("/", 1)[1], summary=summary))
            if len(candidates) >= 25:
                break
        return candidates

    def build_install_plan(self, package_name: str):
        return self.plan("pacman", "Install package with pacman", "pacman", ["-S", "--noconfirm", package_name])
