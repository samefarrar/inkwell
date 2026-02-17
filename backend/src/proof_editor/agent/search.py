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
        from ddgs import DDGS

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
            result = client.search(
                query,
                type="auto",
                num_results=5,
                contents={"text": True},
            )
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


def create_search_provider() -> SearchProvider:
    """Create the default search provider.

    Uses Exa if EXA_API_KEY is set, otherwise falls back to DDG (free).
    """
    exa_key = os.environ.get("EXA_API_KEY", "")
    if exa_key:
        logger.info("Using Exa search provider")
        return ExaSearchProvider(api_key=exa_key)
    logger.info("Using DDG search provider (no EXA_API_KEY)")
    return DDGSearchProvider()
