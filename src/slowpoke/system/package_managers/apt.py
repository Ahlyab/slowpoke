from __future__ import annotations

from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.utils.shell import run_capture


class AptManager(PackageManager):
    name = "apt"

    def search(self, query: str) -> list[PackageCandidate]:
        cp = run_capture(["apt-cache", "search", query])
        if cp.returncode != 0:
            return []
        candidates: list[PackageCandidate] = []
        for line in cp.stdout.splitlines()[:25]:
            if " - " not in line:
                continue
            name, summary = line.split(" - ", 1)
            candidates.append(PackageCandidate(name=name.strip(), summary=summary.strip()))
        return candidates

    def build_install_plan(self, package_name: str):
        return self.plan("apt", "Install package with apt", "apt-get", ["install", "-y", package_name])
