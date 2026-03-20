from __future__ import annotations

from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.utils.shell import run_capture


class DnfManager(PackageManager):
    name = "dnf"

    def search(self, query: str) -> list[PackageCandidate]:
        cp = run_capture(["dnf", "search", query])
        if cp.returncode != 0:
            return []
        out = cp.stdout.splitlines()
        candidates: list[PackageCandidate] = []
        for line in out:
            if "." in line and ":" in line:
                pkg, summary = line.split(":", 1)
                candidates.append(PackageCandidate(name=pkg.strip(), summary=summary.strip()))
            if len(candidates) >= 25:
                break
        return candidates

    def build_install_plan(self, package_name: str):
        return self.plan("dnf", "Install package with dnf", "dnf", ["install", "-y", package_name])
