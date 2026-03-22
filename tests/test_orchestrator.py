from __future__ import annotations

import json
import subprocess

import pytest
import slowpoke.core.orchestrator as orchestrator
from slowpoke.core.orchestrator import build_docs_install_plan
from slowpoke.execution.command_model import CommandStep
from slowpoke.llm.base import LLMClient
from slowpoke.web.search_client import SearchResult


class FakeLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "official docs method",
            "steps": [
                {
                    "executable": "apt-get",
                    "args": ["install", "-y", "ripgrep"],
                    "needs_sudo": True,
                    "rationale": "install package",
                }
            ],
        }


def test_build_docs_install_plan_parses_json_steps():
    llm = FakeLLM()
    docs = [SearchResult(title="rg", url="https://example.com", snippet="Install rg")]
    plan = build_docs_install_plan(llm, "ripgrep", docs)
    assert plan.source == "web+llm"
    assert plan.steps[0].executable == "apt-get"


class CapturingLLM(LLMClient):
    def __init__(self) -> None:
        self.last_user_prompt: str | None = None

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        self.last_user_prompt = user_prompt
        return {
            "reason": "ok",
            "steps": [
                {
                    "executable": "dnf",
                    "args": ["config-manager", "addrepo", "--from-repofile=https://packages.microsoft.com/yumrepos/vscode/config.repo"],
                    "needs_sudo": True,
                    "rationale": "add repo",
                },
                {"executable": "dnf", "args": ["install", "-y", "code"], "needs_sudo": True, "rationale": "ok"},
            ],
        }


def test_build_docs_install_plan_includes_distro_context():
    llm = CapturingLLM()
    docs = [SearchResult(title="code", url="https://example.com", snippet="Install code")]

    build_docs_install_plan(
        llm,
        "vscode",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
    )
    assert llm.last_user_prompt is not None
    payload = json.loads(llm.last_user_prompt)
    assert payload["detected_distro"] == "Fedora Linux 43"
    assert payload["detected_package_manager"] == "dnf"
    assert payload["detected_dnf_variant"] == "unknown"


class LegacyDnfSyntaxLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "legacy syntax",
            "steps": [
                {
                    "executable": "dnf",
                    "args": ["config-manager", "--add-repo", "https://packages.microsoft.com/yumrepos/vscode"],
                    "needs_sudo": True,
                    "rationale": "add repo",
                }
            ],
        }


def test_build_docs_install_plan_normalizes_legacy_dnf_add_repo():
    llm = LegacyDnfSyntaxLLM()
    docs = [SearchResult(title="code", url="https://example.com", snippet="Install code")]
    plan = build_docs_install_plan(
        llm,
        "vscode",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
    )
    assert plan.steps[0].executable == "dnf"
    assert plan.steps[0].args == [
        "config-manager",
        "addrepo",
        "--from-repofile=https://packages.microsoft.com/yumrepos/vscode/config.repo",
    ]


class Dnf5BadRepoFileLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "bad repofile",
            "steps": [
                {
                    "executable": "dnf",
                    "args": [
                        "config-manager",
                        "addrepo",
                        "--from-repofile=https://packages.microsoft.com/yumrepos/vscode/vscode.repo",
                    ],
                    "needs_sudo": True,
                    "rationale": "add repo",
                }
            ],
        }


def test_build_docs_install_plan_normalizes_vscode_repofile_url():
    llm = Dnf5BadRepoFileLLM()
    docs = [SearchResult(title="code", url="https://example.com", snippet="Install code")]
    plan = build_docs_install_plan(
        llm,
        "vscode",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
    )
    assert plan.steps[0].args == [
        "config-manager",
        "addrepo",
        "--from-repofile=https://packages.microsoft.com/yumrepos/vscode/config.repo",
    ]


def test_detect_dnf_variant_dnf5(monkeypatch):
    def fake_run_capture(_args, timeout_s=10):
        return subprocess.CompletedProcess(args=["dnf"], returncode=0, stdout="... addrepo ...", stderr="")

    monkeypatch.setattr(orchestrator, "run_capture", fake_run_capture)
    assert orchestrator.detect_dnf_variant() == "dnf5"


def test_detect_dnf_variant_dnf4(monkeypatch):
    def fake_run_capture(_args, timeout_s=10):
        return subprocess.CompletedProcess(args=["dnf"], returncode=1, stdout="", stderr="no addrepo")

    monkeypatch.setattr(orchestrator, "run_capture", fake_run_capture)
    assert orchestrator.detect_dnf_variant() == "dnf4"


class Dnf5SyntaxLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "dnf5 syntax",
            "steps": [
                {
                    "executable": "dnf",
                    "args": [
                        "config-manager",
                        "addrepo",
                        "--from-repofile=https://packages.microsoft.com/yumrepos/vscode/config.repo",
                    ],
                    "needs_sudo": True,
                    "rationale": "add repo",
                }
            ],
        }


def test_build_docs_install_plan_converts_dnf5_to_dnf4_when_requested():
    llm = Dnf5SyntaxLLM()
    docs = [SearchResult(title="code", url="https://example.com", snippet="Install code")]
    plan = build_docs_install_plan(
        llm,
        "vscode",
        docs,
        distro_name="Fedora Linux 39",
        package_manager_name="dnf",
        dnf_variant="dnf4",
    )
    assert plan.steps[0].args == [
        "config-manager",
        "--add-repo",
        "https://packages.microsoft.com/yumrepos/vscode/config.repo",
    ]


class Dnf5ExecutableLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "uses dnf5 executable",
            "steps": [
                {
                    "executable": "dnf5",
                    "args": ["install", "/tmp/slowpoke-windsurf.rpm"],
                    "needs_sudo": True,
                    "rationale": "install",
                }
            ],
        }


def test_build_docs_install_plan_normalizes_dnf5_executable_name():
    llm = Dnf5ExecutableLLM()
    docs = [SearchResult(title="windsurf", url="https://example.com", snippet="Install windsurf")]
    plan = build_docs_install_plan(
        llm,
        "windsurf",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
        dnf_variant="dnf5",
    )
    assert plan.steps[0].executable == "dnf"
    assert plan.steps[0].args == ["install", "/tmp/slowpoke-windsurf.rpm"]


class Dnf5RepoBaseUrlLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "repo base url",
            "steps": [
                {
                    "executable": "dnf",
                    "args": [
                        "config-manager",
                        "addrepo",
                        "--from-repofile=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/",
                    ],
                    "needs_sudo": True,
                    "rationale": "add repo",
                }
            ],
        }


def test_build_docs_install_plan_converts_dnf5_from_repofile_base_url_to_set_baseurl():
    llm = Dnf5RepoBaseUrlLLM()
    docs = [SearchResult(title="windsurf", url="https://example.com", snippet="Install windsurf")]
    plan = build_docs_install_plan(
        llm,
        "windsurf",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
        dnf_variant="dnf5",
    )
    assert plan.steps[0].args == [
        "config-manager",
        "addrepo",
        "--id=windsurf_stable",
        "--set=baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/",
    ]


class Dnf5UnsupportedAddrepoFlagsLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "uses unsupported dnf5 addrepo flags",
            "steps": [
                {
                    "executable": "dnf",
                    "args": [
                        "config-manager",
                        "addrepo",
                        "--id=windsurf",
                        "--name=Windsurf Repository",
                        "--baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/",
                        "--gpgcheck",
                        "--gpgkey=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf",
                    ],
                    "needs_sudo": True,
                    "rationale": "add repo",
                }
            ],
        }


def test_build_docs_install_plan_normalizes_dnf5_addrepo_flag_shape():
    llm = Dnf5UnsupportedAddrepoFlagsLLM()
    docs = [SearchResult(title="windsurf", url="https://example.com", snippet="Install windsurf")]
    plan = build_docs_install_plan(
        llm,
        "windsurf",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
        dnf_variant="dnf5",
    )
    assert plan.steps[0].args == [
        "config-manager",
        "addrepo",
        "--id=windsurf",
        "--set=name=Windsurf Repository",
        "--set=baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/",
        "--set=gpgcheck=1",
        "--set=gpgkey=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf",
    ]


class ShouldNotBeCalledLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        raise AssertionError("LLM should not be called when direct RPM URL exists")


def test_build_docs_install_plan_prefers_direct_rpm_url_for_dnf():
    llm = ShouldNotBeCalledLLM()
    docs = [
        SearchResult(
            title="Download",
            url="https://example.com/page",
            snippet="Use this file: https://downloads.example.com/windsurf-1.2.3.x86_64.rpm",
        )
    ]
    plan = build_docs_install_plan(
        llm,
        "windsurf",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
        dnf_variant="dnf5",
    )
    assert plan.source == "web+direct-rpm"
    assert plan.steps[0].executable == "curl"
    assert plan.steps[1].executable == "dnf"
    assert plan.steps[1].args[:2] == ["install", "-y"]


class IncompleteDnfPlanLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "incomplete",
            "steps": [
                {"executable": "rpm", "args": ["--import", "https://example.com/key"], "needs_sudo": True, "rationale": "key"},
                {"executable": "dnf", "args": ["install", "windsurf"], "needs_sudo": True, "rationale": "install"},
            ],
        }


class DnfRepoAddLLM(LLMClient):
    """Mimics LLM output that uses dnf5 `dnf repo add` instead of config-manager addrepo."""

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "dnf5 repo add",
            "steps": [
                {
                    "executable": "rpm",
                    "args": ["--import", "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf"],
                    "needs_sudo": True,
                    "rationale": "key",
                },
                {
                    "executable": "dnf",
                    "args": [
                        "repo",
                        "add",
                        "windsurf",
                        "--baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/",
                    ],
                    "needs_sudo": True,
                    "rationale": "repo",
                },
                {"executable": "dnf", "args": ["install", "windsurf"], "needs_sudo": True, "rationale": "install"},
            ],
        }


def test_build_docs_install_plan_accepts_dnf_repo_add_as_repo_setup():
    llm = DnfRepoAddLLM()
    docs = [SearchResult(title="docs", url="https://example.com", snippet="Install windsurf")]
    plan = build_docs_install_plan(
        llm,
        "windsurf",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
        dnf_variant="dnf5",
    )
    assert plan.source == "web+llm"
    assert any(
        s.executable == "dnf" and s.args[:2] == ["config-manager", "addrepo"] for s in plan.steps
    )


def test_normalize_dnf_repository_add_converts_to_config_manager_addrepo():
    step = CommandStep(
        executable="dnf",
        args=[
            "repository",
            "add",
            "--id",
            "windsurf",
            "--name",
            "Windsurf",
            "--baseurl",
            "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/",
            "--gpgkey",
            "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf",
            "--gpgcheck",
            "--enabled",
        ],
        needs_sudo=True,
        rationale="repo",
    )
    out = orchestrator._normalize_dnf_step(step, "dnf5")
    assert out.args[:2] == ["config-manager", "addrepo"]
    assert "--id=windsurf" in out.args
    assert any(a.startswith("--set=baseurl=") for a in out.args)
    assert any(a.startswith("--set=gpgkey=") for a in out.args)


def test_normalize_dnf_install_strips_foreign_arch_suffix(monkeypatch):
    monkeypatch.setattr(orchestrator.platform, "machine", lambda: "x86_64")
    step = CommandStep(
        executable="dnf",
        args=["install", "-y", "windsurf.aarch64"],
        needs_sudo=True,
        rationale="install",
    )
    out = orchestrator._normalize_dnf_step(step, "dnf5")
    assert out.args == ["install", "-y", "windsurf"]


def test_normalize_dnf_install_keeps_matching_arch_suffix(monkeypatch):
    monkeypatch.setattr(orchestrator.platform, "machine", lambda: "x86_64")
    step = CommandStep(
        executable="dnf",
        args=["install", "windsurf.x86_64"],
        needs_sudo=True,
        rationale="install",
    )
    out = orchestrator._normalize_dnf_step(step, "dnf5")
    assert "windsurf.x86_64" in out.args


def test_normalize_dnf_install_keeps_noarch(monkeypatch):
    monkeypatch.setattr(orchestrator.platform, "machine", lambda: "x86_64")
    step = CommandStep(
        executable="dnf",
        args=["install", "fonts-blah.noarch"],
        needs_sudo=True,
        rationale="install",
    )
    out = orchestrator._normalize_dnf_step(step, "dnf5")
    assert "fonts-blah.noarch" in out.args


def test_normalize_dnf_addrepo_rewrites_codeium_yum_arm64_on_x86_64(monkeypatch):
    monkeypatch.setattr(orchestrator.platform, "machine", lambda: "x86_64")
    arm_url = "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum-arm64/repo/"
    step = CommandStep(
        executable="dnf",
        args=[
            "config-manager",
            "addrepo",
            "--id=windsurf",
            f"--set=baseurl={arm_url}",
            "--set=gpgcheck=1",
        ],
        needs_sudo=True,
        rationale="repo",
    )
    out = orchestrator._normalize_dnf_step(step, "dnf5")
    joined = " ".join(out.args)
    assert "yum-arm64" not in joined
    assert "yum/repo" in joined


def test_normalize_dnf_addrepo_keeps_matching_tree(monkeypatch):
    monkeypatch.setattr(orchestrator.platform, "machine", lambda: "x86_64")
    ok_url = "https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/"
    step = CommandStep(
        executable="dnf",
        args=["config-manager", "addrepo", f"--set=baseurl={ok_url}"],
        needs_sudo=True,
        rationale="repo",
    )
    out = orchestrator._normalize_dnf_step(step, "dnf5")
    assert ok_url in " ".join(out.args)


def test_extract_yum_repo_hints_prefers_non_arm64_baseurl():
    docs = [
        SearchResult(
            title="Download",
            url="https://windsurf.com/editor/download",
            snippet=(
                "baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum-arm64/repo/ "
                "baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/ "
                "gpgkey=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf"
            ),
        )
    ]
    hints = orchestrator._extract_yum_repo_hints_from_docs(docs)
    assert hints is not None
    assert "arm64" not in hints["baseurl"].lower()
    assert hints["baseurl"].endswith("/yum/repo/")


WINDSURF_REPO_SNIPPET = """
Download for rpm. baseurl=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/repo/
gpgkey=https://windsurf-stable.codeiumdata.com/wVxQEIWkwPUEAGf3/yum/RPM-GPG-KEY-windsurf
"""


def test_build_docs_install_plan_injects_repo_from_snippets_when_llm_omits_repo():
    """LLM may only output rpm + dnf install (no tee); snippets often still contain baseurl/gpgkey."""
    llm = IncompleteDnfPlanLLM()
    docs = [
        SearchResult(
            title="Download Windsurf Editor",
            url="https://windsurf.com/editor/download",
            snippet=WINDSURF_REPO_SNIPPET,
        )
    ]
    plan = build_docs_install_plan(
        llm,
        "windsurf",
        docs,
        distro_name="Fedora Linux 43",
        package_manager_name="dnf",
        dnf_variant="dnf5",
    )
    assert plan.source == "web+llm"
    assert any(
        s.executable == "dnf" and len(s.args) >= 2 and s.args[0] == "config-manager" and s.args[1] == "addrepo"
        for s in plan.steps
    )


def test_build_docs_install_plan_rejects_incomplete_dnf_install_plan():
    llm = IncompleteDnfPlanLLM()
    docs = [SearchResult(title="docs", url="https://example.com", snippet="steps")]

    with pytest.raises(ValueError, match="no repository setup"):
        build_docs_install_plan(
            llm,
            "windsurf",
            docs,
            distro_name="Fedora Linux 43",
            package_manager_name="dnf",
            dnf_variant="dnf5",
        )
