from __future__ import annotations

from slowpoke.core.orchestrator import build_docs_install_plan
from slowpoke.llm.base import LLMClient
from slowpoke.web.search_client import SearchResult


class FakeLLM(LLMClient):
    def complete_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        return {
            "reason": "official docs method",
            "steps": [
                {
                    "executable": "apt-get",
                    "args": ["install", "-y", "ripgrep"],
                    "needs_sudo": True,
                    "rationale": "install package",
                }
            ],
        }


def test_build_docs_install_plan_parses_json_steps():
    llm = FakeLLM()
    docs = [SearchResult(title="rg", url="https://example.com", snippet="Install rg")]
    plan = build_docs_install_plan(llm, "ripgrep", docs)
    assert plan.source == "web+llm"
    assert plan.steps[0].executable == "apt-get"
