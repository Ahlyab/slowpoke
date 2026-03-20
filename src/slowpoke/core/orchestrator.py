from __future__ import annotations

import json
from pathlib import Path

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


def build_docs_install_plan(llm: LLMClient, query: str, docs: list[SearchResult]) -> CommandPlan:
    system_prompt = _read_prompt("install_plan_from_docs.md")
    user_prompt = json.dumps(
        {
            "requested_app": query,
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
    plan = CommandPlan(source="web+llm", reason=str(response.get("reason", "Web docs install plan")), steps=steps)
    validate_plan(plan)
    return plan


def build_install_plan(
    *,
    llm: LLMClient,
    package_manager: PackageManager,
    package_query: str,
    search_client: SearchClient | None,
) -> CommandPlan:
    candidates = package_manager.search(package_query)
    if candidates:
        package_name = resolve_package_name(llm, package_query, candidates)
        plan = package_manager.build_install_plan(package_name)
        validate_plan(plan)
        return plan

    if search_client is None:
        raise RuntimeError("No package candidates found and web search is disabled.")
    docs = search_client.search(f"Install {package_query} on Linux")
    if not docs:
        raise RuntimeError("No package candidates found and web search returned no results.")
    return build_docs_install_plan(llm, package_query, docs)
