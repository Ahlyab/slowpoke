from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from slowpoke.core.config import Settings
from slowpoke.execution.command_model import CommandPlan, CommandStep
from slowpoke.execution.safety import validate_plan
from slowpoke.llm.base import LLMClient
from slowpoke.llm.providers.chatgpt import create_chatgpt_client
from slowpoke.llm.providers.gemini import create_gemini_client
from slowpoke.llm.providers.grok import create_grok_client
from slowpoke.system.package_managers.base import PackageCandidate, PackageManager
from slowpoke.web.search_client import SearchClient, SearchResult
from slowpoke.web.tavily_client import TavilySearchClient
from slowpoke.utils.shell import run_capture


def _read_prompt(name: str) -> str:
    prompt_path = Path(__file__).resolve().parent.parent / "llm" / "prompts" / name
    return prompt_path.read_text(encoding="utf-8")


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider.")
        return create_gemini_client(settings.gemini_api_key, settings.llm_model)
    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider.")
        return create_chatgpt_client(settings.openai_api_key, settings.llm_model)
    if not settings.xai_api_key:
        raise ValueError("XAI_API_KEY is required for Grok provider.")
    return create_grok_client(settings.xai_api_key, settings.llm_model)


def build_search_client(settings: Settings) -> SearchClient | None:
    if settings.web_search_provider == "none":
        return None
    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY is required when WEB_SEARCH_PROVIDER=tavily.")
    return TavilySearchClient(settings.tavily_api_key)


def resolve_package_name(
    llm: LLMClient,
    package_query: str,
    candidates: list[PackageCandidate],
) -> str:
    system_prompt = _read_prompt("package_resolution.md")
    user_prompt = json.dumps(
        {
            "requested_app": package_query,
            "candidates": [candidate.__dict__ for candidate in candidates],
        }
    )
    response = llm.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
    value = response.get("resolved_package_name")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("LLM failed to provide a resolved package name.")
    return value.strip()


def build_docs_install_plan(
    llm: LLMClient,
    query: str,
    docs: list[SearchResult],
    *,
    distro_name: str | None = None,
    package_manager_name: str | None = None,
    dnf_variant: str | None = None,
) -> CommandPlan:
    if package_manager_name == "dnf":
        direct_rpm_url = _extract_direct_package_url(docs, suffix=".rpm")
        if direct_rpm_url:
            plan = _build_direct_rpm_install_plan(query, direct_rpm_url)
            validate_plan(plan)
            return plan

    system_prompt = _read_prompt("install_plan_from_docs.md")
    user_prompt = json.dumps(
        {
            "requested_app": query,
            "detected_distro": distro_name or "unknown",
            "detected_package_manager": package_manager_name or "unknown",
            "detected_dnf_variant": dnf_variant or "unknown",
            "docs": [result.__dict__ for result in docs],
        }
    )
    response = llm.complete_json(system_prompt=system_prompt, user_prompt=user_prompt)
    steps_raw = response.get("steps", [])
    if not isinstance(steps_raw, list) or not steps_raw:
        raise ValueError("LLM returned no install steps.")
    steps: list[CommandStep] = []
    for item in steps_raw:
        if not isinstance(item, dict):
            continue
        executable = str(item.get("executable", "")).strip()
        args = item.get("args", [])
        if not executable or not isinstance(args, list):
            continue
        steps.append(
            CommandStep(
                executable=executable,
                args=[str(a) for a in args],
                needs_sudo=bool(item.get("needs_sudo", False)),
                rationale=str(item.get("rationale", "")),
            )
        )
    if package_manager_name == "dnf":
        resolved_variant = dnf_variant or detect_dnf_variant()
        steps = [_normalize_dnf_step(step, resolved_variant) for step in steps]
        if _is_incomplete_dnf_repo_plan(steps):
            raise ValueError("LLM plan has dnf install step but no repository setup or direct RPM install step.")
    plan = CommandPlan(source="web+llm", reason=str(response.get("reason", "Web docs install plan")), steps=steps)
    validate_plan(plan)
    return plan


def _extract_direct_package_url(docs: list[SearchResult], *, suffix: str) -> str | None:
    url_pattern = re.compile(r"https?://[^\s'\"<>)]+", re.IGNORECASE)
    wanted = suffix.lower()
    for doc in docs:
        candidates = [doc.url, doc.snippet]
        for text in candidates:
            for raw in url_pattern.findall(text):
                cleaned = raw.rstrip(".,;:)]}\"'")
                path = urlparse(cleaned).path.lower()
                if path.endswith(wanted):
                    return cleaned
    return None


def _build_direct_rpm_install_plan(query: str, rpm_url: str) -> CommandPlan:
    package_slug = "".join(ch if ch.isalnum() else "-" for ch in query.strip().lower()).strip("-") or "package"
    local_rpm = f"/tmp/slowpoke-{package_slug}.rpm"
    return CommandPlan(
        source="web+direct-rpm",
        reason=f"Install from direct RPM artifact found in docs: {rpm_url}",
        steps=[
            CommandStep(
                executable="curl",
                args=["-L", "-o", local_rpm, rpm_url],
                needs_sudo=False,
                rationale="Download distro-specific RPM package artifact.",
            ),
            CommandStep(
                executable="dnf",
                args=["install", "-y", local_rpm],
                needs_sudo=True,
                rationale="Install downloaded RPM using dnf.",
            ),
        ],
    )


def _is_incomplete_dnf_repo_plan(steps: list[CommandStep]) -> bool:
    has_repo_setup = False
    has_direct_rpm_install = False
    has_plain_dnf_install = False

    for step in steps:
        if step.executable != "dnf":
            continue
        args = step.args
        if len(args) >= 2 and args[0] == "config-manager" and args[1] in {"addrepo", "--add-repo"}:
            has_repo_setup = True
        if len(args) >= 2 and args[0] == "install":
            install_targets = [arg for arg in args[1:] if not arg.startswith("-")]
            for target in install_targets:
                target_l = target.lower()
                if target_l.endswith(".rpm") or target.startswith("/") or target.startswith("http://") or target.startswith("https://"):
                    has_direct_rpm_install = True
                else:
                    has_plain_dnf_install = True

    return has_plain_dnf_install and not has_repo_setup and not has_direct_rpm_install


def detect_dnf_variant() -> str:
    cp = run_capture(["dnf", "config-manager", "addrepo", "--help"], timeout_s=10)
    if cp.returncode == 0 and "addrepo" in cp.stdout.lower():
        return "dnf5"
    return "dnf4"


def _normalize_dnf_step(step: CommandStep, dnf_variant: str) -> CommandStep:
    def _normalize_repo_url(url: str) -> str:
        if "packages.microsoft.com/yumrepos/vscode" in url:
            if url.endswith("/config.repo"):
                return url
            return "https://packages.microsoft.com/yumrepos/vscode/config.repo"
        return url

    def _repo_id_from_url(url: str) -> str:
        host = urlparse(url).hostname or "thirdparty"
        candidate = host.split(".")[0].strip().lower().replace("-", "_")
        return candidate or "thirdparty"

    def _normalize_dnf5_addrepo_args(args: list[str]) -> list[str]:
        # dnf5 accepts --id plus repeated --set=KEY=VALUE.
        if args[:2] != ["config-manager", "addrepo"]:
            return args

        out: list[str] = ["config-manager", "addrepo"]
        idx = 2
        while idx < len(args):
            token = args[idx]

            if token.startswith("--id=") or token.startswith("--from-repofile=") or token.startswith("--set="):
                out.append(token)
                idx += 1
                continue
            if token.startswith("--name="):
                out.append(f"--set=name={token.split('=', 1)[1]}")
                idx += 1
                continue
            if token.startswith("--baseurl="):
                out.append(f"--set=baseurl={token.split('=', 1)[1]}")
                idx += 1
                continue
            if token.startswith("--gpgkey="):
                out.append(f"--set=gpgkey={token.split('=', 1)[1]}")
                idx += 1
                continue

            if token == "--id" and idx + 1 < len(args):
                out.append(f"--id={args[idx + 1]}")
                idx += 2
                continue

            if token == "--name" and idx + 1 < len(args):
                out.append(f"--set=name={args[idx + 1]}")
                idx += 2
                continue

            if token == "--baseurl" and idx + 1 < len(args):
                out.append(f"--set=baseurl={args[idx + 1]}")
                idx += 2
                continue

            if token == "--gpgcheck":
                out.append("--set=gpgcheck=1")
                idx += 1
                continue

            if token == "--gpgkey" and idx + 1 < len(args):
                out.append(f"--set=gpgkey={args[idx + 1]}")
                idx += 2
                continue

            out.append(token)
            idx += 1

        return out

    normalized_executable = "dnf" if step.executable == "dnf5" else step.executable
    normalized_step = CommandStep(
        executable=normalized_executable,
        args=step.args,
        needs_sudo=step.needs_sudo,
        rationale=step.rationale,
    )

    if normalized_step.executable == "dnf" and len(normalized_step.args) == 3:
        if normalized_step.args[:2] == ["config-manager", "--add-repo"] and dnf_variant == "dnf5":
            repo_url = _normalize_repo_url(normalized_step.args[2])
            return CommandStep(
                executable="dnf",
                args=["config-manager", "addrepo", f"--from-repofile={repo_url}"],
                needs_sudo=normalized_step.needs_sudo,
                rationale=normalized_step.rationale,
            )
        if normalized_step.args[:2] == ["config-manager", "addrepo"] and dnf_variant == "dnf4":
            flag, _, value = normalized_step.args[2].partition("=")
            if flag == "--from-repofile" and value:
                repo_url = _normalize_repo_url(value)
                return CommandStep(
                    executable="dnf",
                    args=["config-manager", "--add-repo", repo_url],
                    needs_sudo=normalized_step.needs_sudo,
                    rationale=normalized_step.rationale,
                )
        if normalized_step.args[:2] == ["config-manager", "addrepo"] and dnf_variant == "dnf5":
            flag, _, value = normalized_step.args[2].partition("=")
            if flag == "--from-repofile" and value:
                repo_url = _normalize_repo_url(value)
                # dnf5 expects --from-repofile to point to a .repo file URL.
                # If model gives a plain repo/base URL, define repository directly.
                if not repo_url.endswith(".repo"):
                    repo_id = _repo_id_from_url(repo_url)
                    return CommandStep(
                        executable="dnf",
                        args=[
                            "config-manager",
                            "addrepo",
                            f"--id={repo_id}",
                            f"--set=baseurl={repo_url}",
                        ],
                        needs_sudo=normalized_step.needs_sudo,
                        rationale=normalized_step.rationale,
                    )
                return CommandStep(
                    executable="dnf",
                    args=["config-manager", "addrepo", f"--from-repofile={repo_url}"],
                    needs_sudo=normalized_step.needs_sudo,
                    rationale=normalized_step.rationale,
                )
    if normalized_step.executable == "dnf" and dnf_variant == "dnf5":
        normalized_args = _normalize_dnf5_addrepo_args(normalized_step.args)
        return CommandStep(
            executable="dnf",
            args=normalized_args,
            needs_sudo=normalized_step.needs_sudo,
            rationale=normalized_step.rationale,
        )
    return normalized_step


def build_install_plan(
    *,
    llm: LLMClient,
    package_manager: PackageManager,
    package_query: str,
    search_client: SearchClient | None,
    distro_name: str | None = None,
) -> CommandPlan:
    candidates = package_manager.search(package_query)
    if candidates:
        package_name = resolve_package_name(llm, package_query, candidates)
        plan = package_manager.build_install_plan(package_name)
        validate_plan(plan)
        return plan

    if search_client is None:
        raise RuntimeError("No package candidates found and web search is disabled.")
    distro_hint = distro_name or "Linux"
    docs = search_client.search(f"Install {package_query} on {distro_hint} with {package_manager.name}")
    if not docs:
        raise RuntimeError("No package candidates found and web search returned no results.")
    if package_manager.name == "dnf":
        artifact_docs = search_client.search(f"{package_query} {distro_hint} download .rpm")
        if artifact_docs:
            docs.extend(artifact_docs)
    dnf_variant = detect_dnf_variant() if package_manager.name == "dnf" else None
    return build_docs_install_plan(
        llm,
        package_query,
        docs,
        distro_name=distro_name,
        package_manager_name=package_manager.name,
        dnf_variant=dnf_variant,
    )
