from __future__ import annotations

import json
import logging
import os
import urllib.request

from slowpoke.web.search_client import SearchClient, SearchResult

logger = logging.getLogger(__name__)


class TavilySearchClient(SearchClient):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        dev_mode = os.getenv("DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
        }
        if dev_mode:
            safe_payload = dict(payload)
            safe_payload["api_key"] = "***"
            logger.info("Tavily request payload: %s", json.dumps(safe_payload, ensure_ascii=False))
        req = urllib.request.Request(
            url="https://api.tavily.com/search",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode("utf-8"),
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            if dev_mode:
                logger.info("Tavily raw response: %s", raw)
            body = json.loads(raw)
        items = body.get("results", [])
        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
            )
            for item in items
        ]
