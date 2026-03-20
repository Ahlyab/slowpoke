from __future__ import annotations

from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.utils.shell import run_capture


class ApkManager(PackageManager):
    name = "apk"

    def search(self, query: str) -> list[PackageCandidate]:
        cp = run_capture(["apk", "search", query])
        if cp.returncode != 0:
            return []
        return [PackageCandidate(name=line.strip(), summary="") for line in cp.stdout.splitlines()[:25] if line.strip()]

    def build_install_plan(self, package_name: str):
        return self.plan("apk", "Install package with apk", "apk", ["add", package_name])
