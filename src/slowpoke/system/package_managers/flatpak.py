from __future__ import annotations

from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.utils.shell import run_capture


class FlatpakManager(PackageManager):
    name = "flatpak"

    def search(self, query: str) -> list[PackageCandidate]:
        cp = run_capture(["flatpak", "search", query])
        if cp.returncode != 0:
            return []
        candidates: list[PackageCandidate] = []
        for line in cp.stdout.splitlines()[1:26]:
            cols = [c.strip() for c in line.split("\t")]
            if cols:
                candidates.append(PackageCandidate(name=cols[0], summary=cols[1] if len(cols) > 1 else ""))
        return candidates

    def build_install_plan(self, package_name: str):
        return self.plan(
            "flatpak",
            "Install package with flatpak",
            "flatpak",
            ["install", "-y", "flathub", package_name],
        )
