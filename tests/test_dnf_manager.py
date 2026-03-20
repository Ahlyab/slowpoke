from __future__ import annotations

import subprocess

from slowpoke.system.package_managers.dnf import DnfManager


def test_dnf_search_parses_default_output(monkeypatch):
    output = """
Updating and loading repositories:
Repositories loaded.
Matched fields: name (exact)
 vlc.x86_64\tThe cross-platform open-source multimedia framework, player and server
Matched fields: name, summary
 vlc-gui-qt.x86_64\tVLC media player Qt GUI
"""

    def fake_run_capture(_args, timeout_s=60):
        return subprocess.CompletedProcess(args=["dnf", "search", "vlc"], returncode=0, stdout=output, stderr="")

    monkeypatch.setattr("slowpoke.system.package_managers.dnf.run_capture", fake_run_capture)

    results = DnfManager().search("vlc")
    assert results
    assert results[0].name == "vlc.x86_64"
    assert "multimedia framework" in results[0].summary


def test_dnf_search_ignores_noise_lines(monkeypatch):
    output = """
Updating and loading repositories:
Repositories loaded.
Matched fields: summary
 kaffeine.x86_64\tKDE media player based on VLC
"""

    def fake_run_capture(_args, timeout_s=60):
        return subprocess.CompletedProcess(args=["dnf", "search", "vlc"], returncode=0, stdout=output, stderr="")

    monkeypatch.setattr("slowpoke.system.package_managers.dnf.run_capture", fake_run_capture)

    results = DnfManager().search("vlc")
    assert len(results) == 1
    assert results[0].name == "kaffeine.x86_64"


def test_dnf_search_uses_term_fallback(monkeypatch):
    calls: list[list[str]] = []

    def fake_run_capture(args, timeout_s=60):
        calls.append(args)
        if args[-1] == "vlc player":
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="Matched fields: name\n", stderr="")
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=" vlc.x86_64     VLC media player\n",
            stderr="",
        )

    monkeypatch.setattr("slowpoke.system.package_managers.dnf.run_capture", fake_run_capture)

    results = DnfManager().search("vlc player")
    assert results
    assert calls[0][-1] == "vlc player"
    assert calls[1][-1] == "vlc"


def test_dnf_search_returns_empty_when_no_matches(monkeypatch):
    def fake_run_capture(_args, timeout_s=60):
        return subprocess.CompletedProcess(
            args=["dnf", "search", "nope"],
            returncode=0,
            stdout="Updating and loading repositories:\nRepositories loaded.\n",
            stderr="",
        )

    monkeypatch.setattr("slowpoke.system.package_managers.dnf.run_capture", fake_run_capture)

    results = DnfManager().search("nope")
    assert results == []
