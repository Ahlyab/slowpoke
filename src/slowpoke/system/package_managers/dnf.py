from __future__ import annotations

import re

from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.utils.shell import run_capture

_CANDIDATE_SPLIT_RE = re.compile(r"\t+|\s{2,}")


def _parse_candidate_line(line: str) -> PackageCandidate | None:
    stripped = line.strip()
    if not stripped:
        return None

    # Ignore common dnf section/status lines.
    lowered = stripped.lower()
    if lowered.startswith("matched fields:") or lowered.endswith(":"):
        return None

    parts = [part.strip() for part in _CANDIDATE_SPLIT_RE.split(stripped, maxsplit=1) if part.strip()]
    if len(parts) != 2:
        return None

    name, summary = parts[0], parts[1]
    if "." not in name:
        return None
    base, arch = name.rsplit(".", 1)
    if not base or not arch:
        return None

    return PackageCandidate(name=name, summary=summary)


class DnfManager(PackageManager):
    name = "dnf"

    def search(self, query: str) -> list[PackageCandidate]:
        attempts: list[str] = [query]
        query_terms = [part for part in query.split() if part]
        if len(query_terms) > 1:
            attempts.extend(query_terms)

        for term in attempts:
            cp = run_capture(["dnf", "search", term], timeout_s=60)
            if cp.returncode != 0:
                continue

            candidates: list[PackageCandidate] = []
            for line in cp.stdout.splitlines():
                candidate = _parse_candidate_line(line)
                if candidate is not None:
                    candidates.append(candidate)
                if len(candidates) >= 25:
                    break

            if candidates:
                return candidates

        return []

    def build_install_plan(self, package_name: str):
        return self.plan("dnf", "Install package with dnf", "dnf", ["install", "-y", package_name])
