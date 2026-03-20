from __future__ import annotations

import json
import logging
import os
import urllib.request
from dataclasses import dataclass

from slowpoke.llm.base import LLMClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    model: str


class OpenAICompatibleClient(LLMClient):
    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self._config = config

    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        dev_mode = os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
        payload = {
            "model": self._config.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        if dev_mode:
            logger.info("LLM request payload: %s", json.dumps(payload, ensure_ascii=False))
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
            raw = response.read().decode("utf-8")
            if dev_mode:
                logger.info("LLM raw response: %s", raw)
            body = json.loads(raw)
        content = body["choices"][0]["message"]["content"]
        if dev_mode:
            logger.info("LLM message content: %s", content)
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response is not a JSON object.")
        return parsed
