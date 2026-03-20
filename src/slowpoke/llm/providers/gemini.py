from __future__ import annotations

from slowpoke.llm.providers.openai_compatible import OpenAICompatibleClient, OpenAICompatibleConfig


def create_gemini_client(api_key: str, model: str) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        OpenAICompatibleConfig(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai",
            api_key=api_key,
            model=model,
        )
    )
