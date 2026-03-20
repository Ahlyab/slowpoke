from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ProviderName = Literal["gemini", "openai", "grok"]
WebSearchProviderName = Literal["tavily", "none"]


@dataclass(frozen=True)
class Settings:
    llm_provider: ProviderName
    llm_model: str
    openai_api_key: str | None
    gemini_api_key: str | None
    xai_api_key: str | None
    web_search_provider: WebSearchProviderName
    tavily_api_key: str | None
    auto_sudo: bool
    log_level: str
    log_file: Path


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    llm_provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if llm_provider not in {"gemini", "openai", "grok"}:
        raise ValueError("LLM_PROVIDER must be one of: gemini, openai, grok")

    web_search_provider = os.getenv("WEB_SEARCH_PROVIDER", "none").strip().lower()
    if web_search_provider not in {"tavily", "none"}:
        raise ValueError("WEB_SEARCH_PROVIDER must be one of: tavily, none")

    return Settings(
        llm_provider=llm_provider,  # type: ignore[arg-type]
        llm_model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        xai_api_key=os.getenv("XAI_API_KEY"),
        web_search_provider=web_search_provider,  # type: ignore[arg-type]
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        auto_sudo=_env_bool("AUTO_SUDO", True),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        log_file=Path(os.getenv("SLOWPOKE_LOG_FILE", ".slowpoke.log")),
    )
