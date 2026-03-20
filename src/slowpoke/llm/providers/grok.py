from __future__ import annotations

from slowpoke.llm.providers.openai_compatible import OpenAICompatibleClient, OpenAICompatibleConfig


def create_grok_client(api_key: str, model: str) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        OpenAICompatibleConfig(
            base_url="https://api.x.ai/v1",
            api_key=api_key,
            model=model,
        )
    )
