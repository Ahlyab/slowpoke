from __future__ import annotations

import json
import urllib.request

from slowpoke.web.search_client import SearchClient, SearchResult


class TavilySearchClient(SearchClient):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        payload = {
            "api_key": self._api_key,
            "query": query,
            "max_results": max_results,
        }
        req = urllib.request.Request(
            url="https://api.tavily.com/search",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload).encode("utf-8"),
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
        items = body.get("results", [])
        return [
            SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                snippet=item.get("content", ""),
            )
            for item in items
        ]
