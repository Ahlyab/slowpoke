from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

from slowpoke.system.package_managers.apk import ApkManager
from slowpoke.system.package_managers.apt import AptManager
from slowpoke.system.package_managers.base import PackageManager
from slowpoke.system.package_managers.dnf import DnfManager
from slowpoke.system.package_managers.flatpak import FlatpakManager
from slowpoke.system.package_managers.pacman import PacmanManager
from slowpoke.system.package_managers.zypper import ZypperManager


@dataclass(frozen=True)
class LinuxSystemInfo:
    distro_id: str
    version_id: str
    pretty_name: str
    package_manager: str


def _read_os_release() -> dict[str, str]:
    path = Path("/etc/os-release")
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip().strip('"')
    return values


def detect_package_manager_name() -> str | None:
    priority = ["apt-get", "dnf", "pacman", "zypper", "apk", "flatpak"]
    mapping = {
        "apt-get": "apt",
        "dnf": "dnf",
        "pacman": "pacman",
        "zypper": "zypper",
        "apk": "apk",
        "flatpak": "flatpak",
    }
    for cmd in priority:
        if shutil.which(cmd):
            return mapping[cmd]
    return None


def detect_linux_system() -> LinuxSystemInfo:
    if platform.system().lower() != "linux":
        raise RuntimeError("Slowpoke currently supports Linux only.")
    os_release = _read_os_release()
    manager = detect_package_manager_name()
    if not manager:
        raise RuntimeError("No supported Linux package manager found on this system.")
    return LinuxSystemInfo(
        distro_id=os_release.get("ID", "unknown"),
        version_id=os_release.get("VERSION_ID", "unknown"),
        pretty_name=os_release.get("PRETTY_NAME", "Linux"),
        package_manager=manager,
    )


def create_package_manager(name: str) -> PackageManager:
    mapping: dict[str, type[PackageManager]] = {
        "apt": AptManager,
        "dnf": DnfManager,
        "pacman": PacmanManager,
        "zypper": ZypperManager,
        "apk": ApkManager,
        "flatpak": FlatpakManager,
    }
    if name not in mapping:
        raise ValueError(f"Unsupported package manager: {name}")
    return mapping[name]()
