"""Search providers — DDG, Exa, and Anthropic (built-in) web search."""

import logging
import os
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


class SearchResult:
    """A single search result."""

    __slots__ = ("title", "url", "snippet")

    def __init__(self, title: str, url: str, snippet: str) -> None:
        self.title = title
        self.url = url
        self.snippet = snippet

    def to_dict(self) -> dict[str, str]:
        return {"title": self.title, "url": self.url, "snippet": self.snippet}


@runtime_checkable
class SearchProvider(Protocol):
    """Protocol for search providers that use explicit tool calls."""

    async def search(self, query: str) -> list[SearchResult]: ...


class DDGSearchProvider:
    """DuckDuckGo search — no API key required."""

    async def search(self, query: str) -> list[SearchResult]:
        from duckduckgo_search import DDGS

        try:
            results = DDGS().text(query, max_results=5)
            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                )
                for r in results
            ]
        except Exception:
            logger.exception("DDG search failed for query: %s", query)
            return []


class ExaSearchProvider:
    """Exa.ai search — requires EXA_API_KEY."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("EXA_API_KEY", "")

    async def search(self, query: str) -> list[SearchResult]:
        from exa_py import Exa

        try:
            client = Exa(api_key=self.api_key)
            result = client.search_and_contents(query, num_results=5, text=True)
            return [
                SearchResult(
                    title=r.title or "",
                    url=r.url,
                    snippet=(r.text or "")[:300],
                )
                for r in result.results
            ]
        except Exception:
            logger.exception("Exa search failed for query: %s", query)
            return []


def create_search_provider(
    provider_name: str,
) -> SearchProvider | None:
    """Factory: create a search provider by name.

    Returns None for 'anthropic' (handled at LiteLLM level).
    """
    if provider_name == "ddg":
        return DDGSearchProvider()
    elif provider_name == "exa":
        return ExaSearchProvider()
    elif provider_name == "anthropic":
        return None
    else:
        logger.warning("Unknown search provider: %s", provider_name)
        return None
