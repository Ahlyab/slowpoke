from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass

from slowpoke.llm.base import LLMClient


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str


class OpenAICompatibleClient(LLMClient):
    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self._config = config

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        payload = {
            "model": self._config.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        req = urllib.request.Request(
            url=f"{self._config.base_url.rstrip('/')}/chat/completions",
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._config.api_key}",
            },
            data=json.dumps(payload).encode("utf-8"),
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response is not a JSON object.")
        return parsed
