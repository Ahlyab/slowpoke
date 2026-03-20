from __future__ import annotations

from slowpoke.llm.providers.openai_compatible import OpenAICompatibleClient, OpenAICompatibleConfig


def create_chatgpt_client(api_key: str, model: str) -> OpenAICompatibleClient:
    return OpenAICompatibleClient(
        OpenAICompatibleConfig(
            base_url="https://api.openai.com/v1",
            api_key=api_key,
            model=model,
        )
    )
