from __future__ import annotations

import slowpoke.system.system_info as system_info


def test_detect_package_manager_name(monkeypatch):
    def fake_which(cmd: str):
        if cmd == "apt-get":
            return "/usr/bin/apt-get"
        return None

    monkeypatch.setattr(system_info.shutil, "which", fake_which)
    assert system_info.detect_package_manager_name() == "apt"


def test_read_os_release_empty_when_missing(monkeypatch):
    class FakePath:
        def __init__(self, *_args, **_kwargs):
            pass

        def exists(self):
            return False

    monkeypatch.setattr(system_info, "Path", FakePath)
    assert system_info._read_os_release() == {}
