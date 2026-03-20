from __future__ import annotations

from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.utils.shell import run_capture


class ZypperManager(PackageManager):
    name = "zypper"

    def search(self, query: str) -> list[PackageCandidate]:
        cp = run_capture(["zypper", "--non-interactive", "search", query])
        if cp.returncode != 0:
            return []
        candidates: list[PackageCandidate] = []
        for line in cp.stdout.splitlines():
            if "|" not in line:
                continue
            cols = [col.strip() for col in line.split("|")]
            if len(cols) >= 3 and cols[0].isdigit():
                candidates.append(PackageCandidate(name=cols[2], summary=cols[3] if len(cols) > 3 else ""))
            if len(candidates) >= 25:
                break
        return candidates

    def build_install_plan(self, package_name: str):
        return self.plan("zypper", "Install package with zypper", "zypper", ["--non-interactive", "install", package_name])
